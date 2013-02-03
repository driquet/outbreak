'''
File: game.py
Author: Damien Riquet <d.riquet@gmail.com>
Description: Class game describe an outbreak game (initial turn then turns while there is no winner
'''

# imports
import random
import re

import arena
import config
import message
from entity import Genre
from enum import enum
from network import get_player_connection, get_player_message, get_player_message_sequence, send_player_message


score_zombie_lost = -2
score_contagion = 1
score_zombie_killed = 1
score_cop_killed = 5

class OutbreakGame():
    def __init__(self, arena, config, trace):
        self.arena = arena
        self.entities = arena.entities
        self.config  = config
        self.team_scores = [0] * arena.nb_players
        self.players_left = range(1, arena.nb_players + 1)
        self.players_nick = {}
        self.players_message = {}
        self.players_water_discovered = {}
        self.players_connection = {}
        self.turn = 0

        # Global/Turn data
        self.global_data = {}
        self.global_data['zombies_killed'] = 0
        self.global_data['zombies_contagion'] = 0
        self.global_data['human_killed'] = 0
        self.global_data['cop_killed'] = 0
        self.global_data['berzerk_created'] = 0

        self.turn_data = {}
        self.turn_data['zombies_killed'] = 0
        self.turn_data['zombies_contagion'] = 0
        self.turn_data['human_killed'] = 0
        self.turn_data['cop_killed'] = 0
        self.turn_data['berzerk_created'] = 0

        for i in xrange(1, arena.nb_players + 1):
            self.players_message[i] = []
            self.players_water_discovered[i] = []

        self.trace_file = open(trace, 'w')


    def trace_init(self):
        """ Print initial data into the trace file """
        self.trace_file.write(" ".join(self.players_nick.values()) + '\n')
        self.trace_file.write("%d %d\n" % (self.arena.rows, self.arena.cols))


    def trace_turn(self):
        """ Print turn data into the trace file """
        self.trace_file.write("%d\n" % self.turn)
        self.trace_file.write("%s\n" % " ".join([str(elt) for elt in self.team_scores]))

        # Arena representation
        arena_repr = []
        for row in xrange(self.arena.rows):
            arena_repr.append("")

            for col in xrange(self.arena.cols):
                arena_repr[row] += 'w' if self.arena.arena[row][col].surface == arena.Surface.WATER else ' '

        # Places entities on the map
        for entity in self.entities.get_all():
            str_b = arena_repr[entity._row][:entity._col]
            str_e = arena_repr[entity._row][entity._col+1:]
            arena_repr[entity._row] = str_b + entity.get_char_repr() + str_e

        # Send the map
        for row in arena_repr:
            self.trace_file.write("%s\n" % row)


    def manage_player_connection(self, host, port):
        """ Awaits for every player to connect to the server and fill local connections """
        for i in xrange(1, self.arena.nb_players + 1):
            print "Waiting for player #%d to connect" % i
            player_conn = get_player_connection(host, port, self.config.getfloat('initial', 'timing_limit'))
            self.players_connection[i] = player_conn

            # Awaits for nick identification
            msg = get_player_message(player_conn)
            if msg == "":
                # TODO Manage error
                pass

            nick_re = r"nick\s+(\w+)"
            m = re.match(nick_re, msg)

            if not m:
                # TODO Manage message error
                pass

            nick = m.group(1)
            if nick in self.players_nick.values():
                nick += '_'
            self.players_nick[i] = nick

            print "Player #%d connected - nick %s" % (i, nick)

            # Answer back the chosen nick
            send_player_message(player_conn, "nick %s %d\n" % (nick, i))

            # Send initial data
            self.send_initial_data(i)

            # Initial zombie for this player
            for z in self.entities.get_player_zombies(i):
                self.players_message[i].append(message.ZombieMessage(z._id, z._row, z._col))


    def manage_end_game(self):
        """ 
            This function deals with the end of a game
            It sends 'end' message to players left
            then send final data to all players

        """
        print '--- manage_end_game'

        # Send end to players left
        for player in xrange(1, self.arena.nb_players + 1):
            send_player_message(self.players_connection[player], 'end\n')

        # Compute winners/loosers
        loosers = range(1, self.arena.nb_players + 1)

        if len(self.players_left) == 1:
            # Only one player left = winner, others = loosers
            winners = self.players_left
            loosers.remove(winners[0])

        else:
            # No players left or at least two players
            if len(self.players_left) == 0:
                # No players left, look for max score for all players
                possible_winners = range(1, self.arena.nb_players + 1)

            else:
                # Left players, the winner is among them
                possible_winners = self.players_left

            # Look for max
            max_score = max(self.team_scores)

            winners = [player for player in possible_winners if self.team_scores[player - 1] == max_score]
            loosers = [player for player in loosers if player not in winners]

        print 'winners are:', ', '.join([str(elt) for elt in winners])
        print 'loosers are:', ', '.join([str(elt) for elt in loosers])

        # for all players, sends final data
        for player in winners + loosers:
            send_player_message(self.players_connection[player], 'final %d %d\n' % ((1 if player in winners else 0), self.turn))
            send_player_message(self.players_connection[player], 'scores %s\n' % (' '.join([str(elt) for elt in self.team_scores])))
            self.players_connection[player].close()



    def send_initial_data(self, player):
        """ Send the initial data (global data from the configuration file) """
        print "Sending initial data to player #%d" % player

        for option in self.config.options('initial'):
            send_player_message(self.players_connection[player], '%s %f\n' % (option, self.config.getfloat('initial', option)))
            print '%s %f' % (option, self.config.getfloat('initial', option))

        send_player_message(self.players_connection[player], 'end\n')

    
    def compute_turn_data(self):
        """
            In this fonction, we have to compute the data relative to each player
            It includes:
                - new water cells discovered
                - ennemy entity in range 
                - shots made by the player's cops
                - contagions made by the player's zombies
                - player's zombies that made a move
                - player's zombies that are dead
            In this function, we only have to compute (water cells, ennemy entity)
            Other data is computed during turn phases
        """
        print '-- compute_turn_data'
        view_radius = self.config.getfloat('initial', 'view_radius')

        for player in self.players_left:
            print '- player #%d' % player
            visible_entities = []
            new_water = []

            # for each zombie, look for ennemy entities nearby or new water cell
            for z in self.entities.get_player_zombies(player):
                # Look for nearby entities
                for n in self.entities.get_nearest_ennemy_entities(z, view_radius):
                    if n not in visible_entities:
                        visible_entities.append(n)

                # Look for new water cell
                for d_row, d_col in self.arena.relative_visible_cells:
                    f_row = z._row + d_row
                    f_col = z._col + d_col

                    if f_row >= 0 and f_row < self.arena.rows \
                      and f_col >= 0 and f_col < self.arena.cols \
                      and self.arena.arena[f_row][f_col].surface == arena.Surface.WATER \
                      and (f_row, f_col) not in self.players_water_discovered[player]:
                        self.players_water_discovered[player].append((f_row, f_col))
                        new_water.append((f_row, f_col))

            # At this point, we know the data for this player
            # Make messages
            for e in visible_entities:
                self.players_message[player].append(message.EntityMessage(e._row, e._col, e._type, e._team))

            for row, col in new_water:
                self.players_message[player].append(message.WaterMessage(row, col))


    def send_turn_data(self, player):
        """ Sends all messages in the queue then clear the queue """
        print '- send_turn_data - #%d' % player
        player_conn = self.players_connection[player]


        # 1) Send contextual data
        send_player_message(player_conn, 'turn %d\n' % self.turn)
        send_player_message(player_conn, 'players %d\n' % len(self.players_left))
        send_player_message(player_conn, 'scores %s\n' % ' '.join([str(elt) for elt in self.team_scores]))

        for message in self.players_message[player]:
            # Sends the message to the player
            send_player_message(player_conn, message.__str__() + '\n')

        # Clear message queue
        self.players_message[player] = []

        send_player_message(player_conn, 'end\n')



    def get_player_move(self, player):
        moves = []
        movers = []
        
        print '- get_player_move - #%d ' % player
        msg = get_player_message_sequence(self.players_connection[player], self.config.getfloat('initial', 'timing_limit'))
        
        if msg.strip().endswith('end'): 
            for m in re.finditer(r"move\s+(\d+)\s+([N|E|S|W])", msg):
                z_id = int(m.group(1))
                z_dir = m.group(2)

                print 'move %d %s' % (z_id, z_dir)

                # Look for the entity and add the move
                for z in self.entities.get_player_zombies(player):
                    if z._id == z_id:
                        if z_id not in movers:
                            if self.arena.is_valid_move(z, z_dir):
                                moves.append((z, z_dir))
                                movers.append(z_id)
                        break
                

        return moves

    def do_turn(self):
        print '---------------------------'
        print '--- do turn %d' % self.turn

        moves = []

        self.turn_data['zombies_killed'] = 0
        self.turn_data['zombies_contagion'] = 0
        self.turn_data['human_killed'] = 0
        self.turn_data['cop_killed'] = 0
        self.turn_data['berzerk_created'] = 0
        
        # Compute turn data
        self.compute_turn_data()

        # For every player, send current data and wait player moves
        for player in self.players_left:
            self.send_turn_data(player)
            moves += self.get_player_move(player)

        # Add humans/cops/berzerks moves
        moves += self.compute_local_moves()

        # Four steps of a turn
        self.do_move_phase(moves)
        self.do_auto_phase()
        self.do_attack_phase()
        self.do_contagion_phase()

        # Update
        self.turn += 1


    def compute_local_moves(self):
        moves = []

        for entity in self.entities.get_humans() + self.entities.get_cops() + self.entities.get_berzerks():
            moves.append((entity, random.choice(['N', 'S', 'E', 'W'])))

        return moves


    def do_move_phase(self, moves):
        """ 
            Move all the entities
            A move is formatted as follow : (entity, direction)
            Moves are done only at the end of this function
            because we need to find entities that are at the same spot
        """
        print '--- move_phase'
        motionless = self.entities.get_all()[:]
        motion = []
        target_cells = {}

        for entity, direction in moves:
            if self.arena.is_valid_move(entity, direction) and entity not in motion:
                motion.append(entity)
                motionless.remove(entity)

                # update future arena state
                row, col = self.arena.get_targeted_cell(entity, direction)
                if (row, col) not in target_cells:
                    target_cells[(row, col)] = []
                target_cells[(row, col)].append(entity)

        # Add the position of motionless entities
        for entity in motionless:
            row, col = entity._row, entity._col
            if (row, col) not in target_cells:
                target_cells[(row, col)] = []
            target_cells[(row, col)].append(entity)

        # Look for cells with more than one entities AND KILL THEM ALL
        for cell, elts in target_cells.items():
            if len(elts) == 1:
                # Only one entity, valid
                entity = elts[0]
                if entity in motion:
                    entity.move_to(cell[0], cell[1])
                    if entity._type == Genre.ZOMBIE:
                        print 'team %d' % entity._team,
                        self.players_message[entity._team].append(message.ZombieMessage(entity._id, entity._row, entity._col))

            else:
                # More than one entity
                # Kill all these entities
                for entity in elts:
                    self.entities.die(entity)
                    if entity._type == Genre.ZOMBIE:
                        print 'team %d' % entity._team,
                        self.players_message[entity._team].append(message.DeadMessage(entity._id))

                        self.global_data['zombies_killed'] += 1
                        self.turn_data['zombies_killed'] += 1

                        # Updates score
                        self.team_scores[entity._team - 1] += score_zombie_lost

                    
        

    def do_auto_phase(self):
        """ The auto phase manages automatic events like cop shots or berzerk explosion """
        print '--- auto_phase'
        dead_entities = set()
        shot_radius = self.config.getfloat('initial', 'shot_radius')
        shot_success = self.config.getfloat('initial', 'shot_success')
        berzerk_radius = self.config.getfloat('initial', 'berzerk_radius')

        # First, manage human/zombie cops
        cops = self.entities.get_cops()[:] + [zombie for zombie in self.entities.get_zombies() if zombie.has_bullet()]
        for cop in cops:
            ennemy_zombies_in_range = self.entities.get_nearest_ennemy_zombies(cop, shot_radius)

            if len(ennemy_zombies_in_range):
                ennemy = random.sample(ennemy_zombies_in_range, 1)[0]

                cop.remove_bullet()

                if random.random() < shot_success:
                    # Shot successful
                    dead_entities.add(ennemy)
                    if cop._type == Genre.ZOMBIE:
                        self.players_message[cop._team].append(message.ShotMessage(cop._id))

                        # Updates score
                        self.team_scores[cop._team - 1] += score_zombie_killed

                if cop._type == Genre.COP and not cop.has_bullet():
                    self.entities.make_human_from_cop(cop)

        # Then, manage berzerk explosion
        for bzk in self.entities.get_berzerks():
            if bzk.explode_berzerk():
                # Berzerk will explode
                entities_in_range = self.entities.get_nearest_entities(bzk, berzerk_radius)
                dead_entities.add(bzk)
                for entity in entities_in_range:
                    dead_entities.add(entity)

        # Finally, manage dead entities
        for dead in dead_entities:
            if dead._type == Genre.ZOMBIE:
                self.players_message[dead._team].append(message.DeadMessage(dead._id))

                self.global_data['zombies_killed'] += 1
                self.turn_data['zombies_killed'] += 1

                # Updates score
                self.team_scores[dead._team - 1] += score_zombie_lost

            self.entities.die(dead)


    def do_attack_phase(self):
        """
        Look for attack between zombies of different teams
        If a zombie is in range of another zombie of a different team, one or both will die
        """
        print '--- attack_phase'
        attack_radius = self.config.getfloat('initial', 'attack_radius')
        dead_zombies = []

        zombies_ennemy_neighbourhood = {}

        # First we compute only once ennemy neighbourhood
        for zombie in self.entities.get_zombies():
            zombies_ennemy_neighbourhood[zombie] = self.entities.get_nearest_ennemy_zombies(zombie, attack_radius)


        for zombie in self.entities.get_zombies():
            for ennemy_zombie in zombies_ennemy_neighbourhood[zombie]:
                if len(zombies_ennemy_neighbourhood[zombie]) >= len(zombies_ennemy_neighbourhood[ennemy_zombie]):
                    # The actual zombie is marked as dead
                    # He is only removed at the end of the phase
                    if zombie not in dead_zombies:
                        dead_zombies.append(zombie)

                        # Updates score
                        self.team_scores[ennemy_zombie._team - 1] += score_zombie_killed

        # We remove all dead zombies
        for zombie in dead_zombies:
            self.players_message[zombie._team].append(message.DeadMessage(zombie._id))


            self.global_data['zombies_killed'] += 1
            self.turn_data['zombies_killed'] += 1

            # Updates score
            self.team_scores[zombie._team - 1] += score_zombie_lost

            self.entities.die(zombie)


    def do_contagion_phase(self):
        """
        Look for contagion among humans
        A contagion could happen if a human has at least one zombie near him
        """
        print '--- contagion_phase'
        contagion_radius = self.config.getfloat('initial', 'contagion_radius')
        
        for human in self.entities.get_humans():
            zombies = self.entities.get_nearest_zombies(human, contagion_radius)

            if len(zombies):
                # There is at least a zombie near this human

                if len(zombies) > 1:
                    # If there is more than one zombie, we select the player who has the most zombies near this human
                    zombies_owner = {}
                    for zombie in zombies:
                        if zombie._team not in zombies_owner:
                            zombies_owner[zombie._team] = 0
                        zombies_owner[zombie._team] += 1

                    # Look for the max number of zombies for each team
                    max_zombies = max(zombies_owner.values())

                    # Which team have 'max_zombies' near this human
                    valid_teams = [team for team,nb in zombies_owner.items() if nb==max_zombies]

                    # Select one team randomnly
                    team = random.sample(valid_teams, 1)[0]
                    team_zombies = [zombie for zombie in zombies if zombie._team == team]

                    # Then select the zombie of this team with the higher contagion counter
                    zombie = max(team_zombies, key=lambda e: e._contagion)

                else:
                    zombie = zombies[0]
                    team = zombie._team

                # At this point, we know the zombie that tries to infect the human
                contagion_amount = self.config.getint('initial', 'contagion_amount')
                p_contagion = float(zombie._contagion) / contagion_amount
                
                if random.random() < p_contagion:
                    # Infection
                    self.entities.contaminate_human(zombie, human, contagion_amount)
                    self.players_message[zombie._team].append(message.ContagionMessage(zombie._id, human._id, human._row, human._col, human._bullet))

                    self.global_data['zombies_contagion'] += 1
                    self.turn_data['zombies_contagion'] += 1

                    # Updates scores
                    if human.has_bullet():
                        self.team_scores[team - 1] += score_cop_killed
                    else:
                        self.team_scores[team - 1] += score_contagion

                else:
                    # No infection
                    # In this case, we need to know if the human dies or transforms into a berzerk
                    p_berzerk = (float(contagion_amount - zombie._contagion) / contagion_amount) * 0.25

                    if random.random() < p_berzerk:
                        # Creation of a berzerk
                        self.entities.create_berzerk(human, self.config.getint('initial', 'berzerk_delay'))

                        self.global_data['berzerk_created'] += 1
                        self.turn_data['berzerk_created'] += 1

                        
                    else:
                        # Human dies - remove him from the map an from the list

                        # Updates scores
                        if human.has_bullet():
                            self.team_scores[team - 1] += score_cop_killed

                        self.global_data['human_killed'] += 1
                        self.turn_data['human_killed'] += 1


                        self.entities.die(human)


    def check_end_condition(self):
        """
        This function checks if end conditions are reached or not.
        It also remove beaten players.

        The game is finished when :
            - TURN_MAX turns
            - Only 1 player left (or less)
        
        @return: True if the game is finished, False otherwise

        """
        # Remove beater players
        for player in self.players_left:
            if not len(self.entities.get_player_zombies(player)):
                self.players_left.remove(player)

        # TURN_MAX reached ?
        if self.turn == self.config.getint('initial', 'turn_max'):
            return True

        # Less than 2 player left ?
        if len(self.players_left) < 2:
            return True

        # Game not finished
        return False


    def do_game(self, host, port):
        """
            This function manage a whole game :
                - awaits players to be connected
                - play turn
                    - check for end conditions
                    - remove players that have lost
                - disconnect players
        """
        # 1) Awaits players to be connected
        #    That part sends initial data to players
        self.manage_player_connection(host, port)
        self.trace_init()

        # 2) Play turn until there is no end condition reached 
        finished = False
        while not finished:
            self.print_game_data()
            self.trace_turn()
            self.do_turn()

            if self.check_end_condition():
                # End condition reached
                finished = True

        # 3) Send final data and disconnect players
        self.trace_turn()
        self.manage_end_game()


    def print_game_data(self):
        """ This function print the current state of the arena """ 
        print '----- Game data ------'
        
        for player in xrange(1, self.arena.nb_players + 1):
            print ' Player #%d - score %d : %d zombies left' % (player, self.team_scores[player - 1], len(self.entities.get_player_zombies(player)))


        print ' Humans: %d left' % (len(self.entities.get_humans()))
        print ' Cops : %d left' % (len(self.entities.get_cops()))
        print ' Berzerks : %d left' % (len(self.entities.get_berzerks()))
        
        print '%20s %10s %10s' % ('', 'global', 'last turn')
        for key in self.global_data:
            print '%20s %10d %10d' % (key, self.global_data[key], self.turn_data[key])
        
        print '----- Game data ------'
            



