# qlearningAgents.py
# ------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

from game import *
from learningAgents import ReinforcementAgent
from featureExtractors import *
from shield import Shield
from stormEncoder import StormEncoder
import numpy as np

import random, util, math, copy
 
RIGHT = 0
UP = 1
LEFT = 2
DOWN = 3
TOP_RIGHT = 4
TOP_LEFT = 5
BOTTOM_RIGHT = 6
BOTTOM_LEFT = 7
STOP = 8

STR_RIGHT = "r"
STR_UP = "u"
STR_LEFT = "l"
STR_DOWN = "d"
STR_TOP_RIGHT = "u-r"
STR_TOP_LEFT = "u-l"
STR_BOTTOM_RIGHT = "d-r"
STR_BOTTOM_LEFT = "d-l"
STR_STOP = "s"

MAX_TIME_COLORED = 3
PROB_LIMIT_SAFE_ACTION = 0.2

class QLearningAgent(ReinforcementAgent):
    """
      Q-Learning Agent

      Functions you should fill in:
        - computeValueFromQValues
        - computeActionFromQValues
        - getQValue
        - getAction
        - update

      Instance variables you have access to
        - self.epsilon (exploration prob)
        - self.alpha (learning rate)
        - self.discount (discount rate)

      Functions you should use
        - self.getLegalActions(state)
          which returns legal actions for a state
    """
    def __init__(self, **args):
        "You can initialize Q-values here..."
        ReinforcementAgent.__init__(self, **args)
        self.qValues = util.Counter()

    def getQValue(self, state, action):
        """
          Returns Q(state,action)
          Should return 0.0 if we have never seen a state
          or the Q node value otherwise
        """
        return self.qValues[(state,action)]


    def computeValueFromQValues(self, state):
        """
          Returns max_action Q(state,action)
          where the max is over legal actions.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return a value of 0.0.
        """
        valuesForActions = util.Counter()
        for action in self.getLegalActions(state):
            valuesForActions[action] = self.getQValue(state,action)
        return valuesForActions[valuesForActions.argMax()]

    def computeActionFromQValues(self, state, safeActions = None):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        valuesForActions = util.Counter()

        if safeActions == None:
            for action in self.getLegalActions(state):
                valuesForActions[action] = self.getQValue(state,action)
        else:
            for action in safeActions:
                valuesForActions[action] = self.getQValue(state,action)

        return valuesForActions.argMax()

    def getProbabilityFromShield(self, state):

        height = state.data.layout.height

        # get pos from pacman
        x_pac = state.getPacmanPosition()[0]
        y_pac = height - state.getPacmanPosition()[1] - 1

        # assert(self.encoder.isCrossing(x_pac, y_pac))

        nh = self.encoder.neighborHood([x_pac, y_pac])

        probs = []

        if not self.encoder.isWall(nh[0]):
            prob_down = self.getProbabilityFromShieldPerDirection(state, DOWN)
            probs.append((DOWN, prob_down))
        else:
            probs.append((DOWN, -1))

        if not self.encoder.isWall(nh[1]):
            prob_up = self.getProbabilityFromShieldPerDirection(state, UP)
            probs.append((UP, prob_up))
        else:
            probs.append((UP, -1))

        if not self.encoder.isWall(nh[2]):
            prob_left = self.getProbabilityFromShieldPerDirection(state, LEFT)
            probs.append((LEFT, prob_left))
        else:
            probs.append((LEFT, -1))

        if not self.encoder.isWall(nh[3]):
            prob_right = self.getProbabilityFromShieldPerDirection(state, RIGHT)
            probs.append((RIGHT, prob_right))
        else:
            probs.append((RIGHT, -1))
        print(x_pac, y_pac)
        print(probs)
        print(state)
        return probs

    def convertFromStormDirToPacDir(self, direction):

        if direction == RIGHT:
            return "East"
        if direction == LEFT:
            return "West"
        if direction == UP:
            return "South"
        if direction == DOWN:
            return "North"
        if direction == STOP:
            return "Stop"
    
    def getSafeActionsFromShield(self, state):

        probs = self.getProbabilityFromShield(state)

        safe_actions = []
        for entry in probs:
            if entry[1] >=0 and entry[1] <= PROB_LIMIT_SAFE_ACTION:
                safe_actions.append(self.convertFromStormDirToPacDir(entry[0]))
        print(safe_actions)
        return safe_actions

    def getProbabilityFromShieldPerDirection(self, state, dir_pac):

        height = state.data.layout.height

        # get pos from pacman
        x_pac = state.getPacmanPosition()[0]
        y_pac = height - state.getPacmanPosition()[1] - 1

        # get ghosts dir and pos
        pos_ghosts = state.getGhostPositions()

        dir_ghosts = []
        for i in range(0, len(pos_ghosts)):
            dir_ghosts.append(self.convertCardinalDirection(state.getGhostDirection(i + 1)))

        conv_pos_ghosts = []
        for i in range(0, len(pos_ghosts)):
            x_ghost = int(pos_ghosts[i][0])
            y_ghost = int(height - pos_ghosts[i][1] - 1)
            conv_pos_ghosts.append([x_ghost, y_ghost])

        # get probability from shield
        if dir_pac == STOP:
            return 1.0

        for i in range(0, len(dir_ghosts)):
            if dir_ghosts[i] == STOP:
                return 0.0

        #print("getFromShieldProbabilityToGetEaten: "+str(x_pac)+" "+str(y_pac)+" "+str(dir_pac)+" "+str(conv_pos_ghosts)+" "+str(dir_ghosts))
        res = self.shielder.getFromShieldProbabilityToGetEaten([x_pac, y_pac], dir_pac, conv_pos_ghosts, dir_ghosts)
        return res

    def getVisibilityMap(self, state):
        horizon = self.horizon
        # print("Hor", horizon, self.lookAhead)
        height = state.data.layout.height
        width = state.data.layout.width
        # print(type(state.data.layout.layoutText))
        layout = np.array([list(line) for line in state.data.layout.layoutText])
        # layout = np.empty((height, width), dtype=char)
        layout[True] = '.'
        # print(layout)
        # print(layout.shape)
        walls = np.array(state.getWalls().data).T
        # print(walls.shape)
        walls = np.array([list(line) for line in walls])
        layout[walls] = '%'
        layout = np.flip(layout, axis=0)
        # print("Walls")
        # print(type(walls))
        # print(walls)
        ghosts = state.getGhostPositions()
        for ghost in ghosts:
            print(ghost)
            layout[int(height - ghost[1]-1)][int(ghost[0])] = 'G'
        # pacman = np.array(np.where(layout=='P')).T[0]
        pacman = state.getPacmanPosition()
        pacman = [height-int(pacman[1])-1, int(pacman[0])]
        layout[pacman[0]][pacman[1]] = 'P'
        # print("LL")
        # print(layout.shape)
        # print(layout)
        visible = np.zeros(layout.shape)
        min_depth = (layout!='%')+0.0
        min_depth[min_depth == 1] = np.inf
        # print(min_depth)
        st = []
        node = list(pacman)
        # print(node)
        node.append(0)
        min_depth[node[0],node[1]] = 0
        st.append(node)
        while len(st) > 0:
            top = st[-1]
            if top[2] < horizon:
                if top[0] > 0 and min_depth[top[0]-1][top[1]] > min_depth[top[0]][top[1]]+1:
                    min_depth[top[0]-1, top[1]] = min_depth[top[0]][top[1]]+1
                    node = [top[0]-1, top[1], top[2]+1]
                    st.append(node)
                elif top[1] > 0 and min_depth[top[0]][top[1]-1] > min_depth[top[0]][top[1]]+1:
                    min_depth[top[0], top[1]-1] = min_depth[top[0]][top[1]]+1
                    node = [top[0], top[1]-1, top[2]+1]
                    st.append(node)
                elif top[0] < layout.shape[0]-1 and min_depth[top[0]+1][top[1]] > min_depth[top[0]][top[1]]+1:
                    min_depth[top[0]+1, top[1]] = min_depth[top[0]][top[1]]+1
                    node = [top[0]+1, top[1], top[2]+1]
                    st.append(node)
                elif top[1] < layout.shape[1]-1 and min_depth[top[0]][top[1]+1] > min_depth[top[0]][top[1]]+1:
                    min_depth[top[0], top[1]+1] = min_depth[top[0]][top[1]]+1
                    node = [top[0], top[1]+1, top[2]+1]
                    st.append(node)
                else:
                    visible[top[0], top[1]] = 1
                    st.pop()
            else:
                visible[top[0], top[1]] = 1
                st.pop()
        final_visibility = layout
        final_visibility[visible!=1] = '?'
        # print(final_visibility)
        return final_visibility
    
    def getSafeActions(self, state, actions, legalActions):
        look_ahead = self.lookAhead
        # np.array(np.where(layout=='P')).T
        visibility_map = self.getVisibilityMap(state)
        # pacman = (np.array(np.where(visibility_map=='P')).T)[0]
        height = state.data.layout.height
        pacman = state.getPacmanPosition()
        pacman = [height-pacman[1]-1, pacman[0]]
        safety_map = np.zeros(visibility_map.shape)
        safety_map[visibility_map=='?'] = -1
        safety_map[visibility_map=='G'] = 1
        ghosts = np.array(np.where(visibility_map=='G')).T.tolist()
        ghosts = [tuple(ghost) for ghost in ghosts]
        # min_depth = (visibility_map!='?')+0.0
        # min_depth[min_depth == 1] = np.inf
        ghost_set =np.zeros(visibility_map.shape)
        
        print("Vis Map")
        for line in visibility_map:
            print("".join(line))
        for ghost in ghosts:
            print(ghost)
            ghost_set[ghost[0]][ghost[1]] = 1
        
        ghost_maps = []
        ghost_maps.append(ghost_set)
        for i in range(look_ahead+1):
            prev_ghost_set = ghost_set
            ghost_set = np.zeros(visibility_map.shape)
            prev_ghosts = list(set(ghosts))
            ghosts=[]
            for ghost in prev_ghosts:
                ghosts.append(ghost)
                if ghost[0]>0 and visibility_map[ghost[0]-1][ghost[1]] != '?':
                    ghost_set[ghost[0]-1][ghost[1]] = 1
                    ghosts.append((ghost[0]-1, ghost[1]))
                if ghost[1]>0 and visibility_map[ghost[0]][ghost[1]-1] != '?':
                    ghost_set[ghost[0]][ghost[1]-1] = 1
                    ghosts.append((ghost[0], ghost[1]-1))
                if ghost[0]<ghost_set.shape[0]-1 and visibility_map[ghost[0]+1][ghost[1]] != '?':
                    ghost_set[ghost[0]+1][ghost[1]] = 1
                    ghosts.append((ghost[0]+1, ghost[1]))
                if ghost[1]<ghost_set.shape[1]-1 and visibility_map[ghost[0]][ghost[1]+1] != '?':
                    ghost_set[ghost[0]][ghost[1]+1] = 1
                    ghosts.append((ghost[0], ghost[1]+1))
            ghost_maps.append(ghost_set)

        pacman_maps = np.zeros((look_ahead+1, visibility_map.shape[0], visibility_map.shape[1])      )  
        action_prob_map = []
        final_action_map = []
        pacman_maps[look_ahead] = ghost_maps[look_ahead]
        level = look_ahead-1
        
        while level >=0:
            cells = np.array(np.where(visibility_map!='?')).T.tolist()
            pacman_safety_map = np.ones(visibility_map.shape)
            action_prob = {}
            # final_action = np.copy(visibility_map)
            for action in actions:
                action_safety_map = np.zeros(visibility_map.shape)
                # for i in range(len(transition_prob[action])):

                temp = np.zeros(visibility_map.shape)
                if action=="North":
                    dist = 1
                    axis = 0
                elif action=="West":
                    dist = 1
                    axis = 1
                elif action=="East":
                    dist = -1
                    axis = 1
                elif action=="South":
                    dist = -1
                    axis = 0
                elif action=="Stop":
                    dist=0
                    axis=0
                else:
                    print("INVALID ACTION")
                vis_shift = np.roll(visibility_map, dist, axis=axis)
                pacman_shift = np.roll(pacman_maps[level+1], dist,axis=axis)
                b_check = np.ones(visibility_map.shape)
                b_check[0][:] = 0
                mask = np.logical_and(np.array(vis_shift != '%'), np.array(vis_shift != '?'))
                mask = np.logical_and(mask, b_check)
                temp = (pacman_shift*(mask == True) + pacman_maps[level+1]*(mask==False))
                # action_safety_map = np.maximum(action_safety_map, temp)
                action_safety_map += temp
                    
                pacman_safety_map = np.minimum(action_safety_map, pacman_safety_map)
                # final_action[pacman_safety_map==action_safety_map] = action[0]
                action_prob[action] = action_safety_map
            # final_action[visibility_map == '?'] = '?'
            # print("Final Action: ")
            # print(final_action)
            action_prob_map.insert(0, action_prob)     
            # final_action_map.insert(0, final_action)
            pacman_safety_map[ghost_maps[level] == 1] = 1
            # pacman_safety_map[visibility_map == '%'] = 4
            pacman_safety_map[visibility_map == '?'] = 1
            pacman_maps[level] = pacman_safety_map                       
            level -= 1
            
        if look_ahead > 0:
            safety_map = pacman_maps[0]
            action_map = action_prob_map[0]  
            final_actions = []
            # print(action_map)
            if "North" in legalActions:
                print("North:", action_map["North"][pacman[0]-1][pacman[1]])
                if action_map["North"][pacman[0]-1][pacman[1]] <0.2:
                    final_actions.append("North")
            if "West" in legalActions:
                print("West:", action_map["West"][pacman[0]][pacman[1]-1])
                if action_map["West"][pacman[0]][pacman[1]-1] <0.2:
                    final_actions.append("West")
            if "East" in legalActions:
                print("East:", action_map["East"][pacman[0]][pacman[1]+1])
                if action_map["East"][pacman[0]][pacman[1]+1] <0.2:
                    final_actions.append("East")
            if "South" in legalActions:
                print("South:", action_map["South"][pacman[0]+1][pacman[1]])
                if action_map["South"][pacman[0]+1][pacman[1]] <0.2:
                    final_actions.append("South")
            if "Stop" in legalActions:
                print("Stop:", action_map["Stop"][pacman[0]][pacman[1]])
                if action_map["Stop"][pacman[0]][pacman[1]] <0.2:
                    final_actions.append("Stop")
        else:
            final_actions = legalActions
        print("GetSafeActions")
        print(pacman)
        print(state.getPacmanPosition())
        print(state)
        # print(visibility_map)
        print(legalActions)
        print(final_actions)
        return final_actions


    def getAction(self, state):
        """
          Compute the action to take in the current state.  With
          probability self.epsilon, we should take a random action and
          take the best policy action otherwise.  Note that if there are
          no legal actions, which is the case at the terminal state, you
          should choose None as the action.

          HINT: You might want to use util.flipCoin(prob)
          HINT: To pick randomly from a list, use random.choice(list)!!!!!
        """
        # Pick Action
        actions = ["North", "South", "East", "West", "Stop"]
        legalActions = self.getLegalActions(state)
        randomAction = random.choice(legalActions)
        bestAction = self.computeActionFromQValues(state)

        height = state.data.layout.height

        # get pos from pacman
        x_pac = state.getPacmanPosition()[0]
        y_pac = height - state.getPacmanPosition()[1] - 1
        safeActions = legalActions
        
        if self.localizedShield > 0:
            # if self.episodesSoFar > self.numGhostTraining:
            safeActions = self.getSafeActions(state, actions, legalActions)
        elif self.shielder != None and self.withoutShield==0:
            if self.episodesSoFar > self.numGhostTraining:
                if self.encoder.isCrossing(x_pac, y_pac):
                    safeActions = self.getSafeActionsFromShield(state)
                    #if len(safeActions)==0:
                    #    print(x_pac, y_pac)
                    #print("safe actions, self.episodesSoFar:", safeActions, self.episodesSoFar)

        if len(safeActions)>0:
            randomAction = random.choice(safeActions)
            bestAction = self.computeActionFromQValues(state, safeActions)

        #delta_epsilon = 1 - self.episodesSoFar * float(1/(self.numTraining+self.numGhostTraining)) #linear
        delta_epsilon = (self.numTraining+self.numGhostTraining)/((self.episodesSoFar+1)*(self.episodesSoFar+1))
        curr_epsilon = self.epsilon * delta_epsilon
        print(curr_epsilon)
        input()
        # print("State start: ")
        # # print(state)
        # # print(state.getWalls())
        # # print(state.data.layout)
        # print(legalActions)
        # print(safeActions)
        # print(state.getPacmanPosition())
        # print("State end")

        if util.flipCoin(curr_epsilon):
            print("Random", randomAction)
            print("State end")
            return randomAction
        else:
            print("Best", bestAction)
            print("State end")
            return bestAction

    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """

        estimatedQ = reward + self.discount * self.computeValueFromQValues(nextState)
        runningQ = (1-self.alpha) * self.getQValue(state,action) + self.alpha * estimatedQ
        self.qValues[(state,action)] = runningQ

        self.prev.state = state

    def getPolicy(self, state):
        return self.computeActionFromQValues(state)

    def getValue(self, state):
        return self.computeValueFromQValues(state)


class PacmanQAgent(QLearningAgent):
    "Exactly the same as QLearningAgent, but with different default parameters"

    def __init__(self, epsilon=0.05,gamma=0.8,alpha=0.2, numTraining=0, numGhostTraining=0, withoutShield=0, localizedShield=0, lookAhead=0, **args):
        """
        These default parameters can be changed from the pacman.py command line.
        For example, to change the exploration rate, try:
            python pacman.py -p PacmanQLearningAgent -a epsilon=0.1

        alpha    - learning rate
        epsilon  - exploration rate
        gamma    - discount factor
        numTraining - number of training episodes, i.e. no learning after these many episodes
        numGhostTraining - number of training episodes to learn the model of the ghosts
        """
        args['epsilon'] = epsilon
        args['gamma'] = gamma
        args['alpha'] = alpha
        args['numTraining'] = numTraining
        args['numGhostTraining'] = numGhostTraining
        args['withoutShield'] = withoutShield
        args['localizedShield'] = localizedShield
        args['lookAhead'] = lookAhead
        # args['horizon'] = 2*lookAhead

        self.index = 0  # This is always Pacman

        QLearningAgent.__init__(self, **args)


    def getAction(self, state):
        """
        Simply calls the getAction method of QLearningAgent and then
        informs parent of action for Pacman.  Do not change or remove this
        method.
        """
        action = QLearningAgent.getAction(self,state)
        self.doAction(state,action)
        return action


class ApproximateQAgent(PacmanQAgent):
    """
       ApproximateQLearningAgent

       You should only have to overwrite getQValue
       and update.  All other QLearningAgent functions
       should work as is.
    """
    def __init__(self, extractor='IdentityExtractor', **args):
        self.featExtractor = util.lookup(extractor, globals())()
        PacmanQAgent.__init__(self, **args)
        self.weights = util.Counter()
        self.ghost_weights = util.Counter()
        self.counter = 0
        self.encoded = False
        # ghostTable: Stores behaviour of the ghosts. We assume, all ghosts follow the same strategy.
        self.ghostTable = []
        self.color_counter = 0
        self.encoder = None
        self.shielder = None

    def getWeights(self):
        return self.weights

    def getQValue(self, state, action):
        """
          Should return Q(state,action) = w * featureVector
          where * is the dotProduct operator
        """
        qValue = 0.0
        features = self.featExtractor.getFeatures(state, action)

        for key in list(features.keys()):
            qValue = qValue + self.weights[key] * features[key]
        return qValue


    def updateGhostTable(self, state, next_state):

        c_pos_ghosts = state.getGhostPositions()
        n_pos_ghosts = next_state.getGhostPositions()

        height = state.data.layout.height

        ghost_count = 0
        for c_pos_ghost in c_pos_ghosts:
            x_cghost = int(c_pos_ghost[0])
            y_cghost = int(height - c_pos_ghost[1] - 1)
            dir_cghost = self.convertCardinalDirection(state.getGhostDirection(ghost_count+1))

            if self.encoder:
                if self.encoder.isCrossing(x_cghost, y_cghost):

                    x_nghost = n_pos_ghosts[ghost_count][0]
                    y_nghost = height - n_pos_ghosts[ghost_count][1] - 1
                    dir_nghost = self.convertCardinalDirection(next_state.getGhostDirection(ghost_count + 1))

                    x_pacman = state.getPacmanPosition()[0]
                    y_pacman = height - state.getPacmanPosition()[1] - 1

                    # direction of movement of ghost
                    # (double check: compute the direction also by hand)
                    dir_ghost = None
                    if x_nghost > x_cghost and y_cghost == y_nghost:
                        dir_ghost = RIGHT

                    if x_cghost > x_nghost and y_cghost == y_nghost:
                        dir_ghost = LEFT

                    if x_cghost == x_nghost and y_cghost < y_nghost:
                        dir_ghost = UP

                    if x_cghost == x_nghost and y_nghost < y_cghost:
                        dir_ghost = DOWN

                    if x_cghost == x_nghost and y_nghost == y_cghost:
                        dir_ghost = STOP

                    # Store the behavior of the ghost
                    # if the ghost is at a crossing, in which direction does it move depending on the positioning of pacman

                    crossing_id_ghost = self.encoder.getCrossingIDAtPos(x_cghost, y_cghost)
                    positioning_pacman = self.getDirectionPacmanToGhost(x_cghost, y_cghost, x_pacman, y_pacman)

                    if dir_ghost != STOP:
                        value = 0
                        for rowcount in range(0, len(self.ghostTable)):  # get current entry
                            r = self.ghostTable[rowcount]

                            if r[0] == crossing_id_ghost and r[1] == dir_cghost and r[2] == positioning_pacman and r[3] == dir_ghost:
                                new_row = (crossing_id_ghost, dir_cghost, positioning_pacman, dir_ghost, (r[4] + 1))
                                value = r[4]
                                self.ghostTable[rowcount] = new_row

                        if value == 0:  # create new list entry
                            self.ghostTable.append((crossing_id_ghost, dir_cghost, positioning_pacman, dir_ghost, 1))

                ghost_count += 1

        self.counter += 1

    def getDirectionFromAgent(self, c_pos, n_pos):

        x = c_pos[0]
        y = c_pos[1]
        n_x = n_pos[0]
        n_y = n_pos[1]

        direction = None
        if n_x > x and y == n_y:
            direction = RIGHT

        if x > n_x and y == n_y:
            direction = LEFT

        if x == n_x and y < n_y:
            direction = UP

        if x == n_x and n_y < y:
            direction = DOWN

        if x == n_x and n_y == y:
            direction = STOP

        return direction


    def convertProbToColor(self, prob):
        if prob>-0.002 and prob<=0.1:
            return "GREEN"
        if prob>0.1 and prob<=0.3:
            return "YELLOW"
        if prob>0.3 and prob<=0.5:
            return "GOLD"
        if prob>0.5 and prob<=0.7:
            return "ORANGE"
        if prob > 0.7 and prob <= 0.9:
            return "ORANGERED"
        if prob>0.9 and prob<=1.002:
            return "RED"
        assert(False)

    def colorInCrossing(self, state, next_state):
        # whenever pacman visits a crossing, color in all corridors from this crossing based on the probabilities from the shield

        height = state.data.layout.height
        x_pac = state.getPacmanPosition()[0]
        y_pac = height - state.getPacmanPosition()[1] - 1

        if self.color_counter == MAX_TIME_COLORED:
            self.color_counter == 0
            next_state.data.removeAllColorFields()

        if self.color_counter > 0 and self.color_counter < MAX_TIME_COLORED:
            self.color_counter += 1

        if self.encoder.isCrossing(x_pac, y_pac):

            next_state.data.removeAllColorFields()
            nh = self.encoder.neighborHood([x_pac, y_pac])

            if not self.encoder.isWall(nh[0]):
                prob = self.getProbabilityFromShieldPerDirection(state, DOWN)
                next_state.data.addColorField(nh[0][0], height - nh[0][1] - 1, self.convertProbToColor(prob))

            if not self.encoder.isWall(nh[1]):
                prob = self.getProbabilityFromShieldPerDirection(state, UP)
                next_state.data.addColorField(nh[1][0], height - nh[1][1] - 1, self.convertProbToColor(prob))

            if not self.encoder.isWall(nh[2]):
                prob = self.getProbabilityFromShieldPerDirection(state, LEFT)
                next_state.data.addColorField(nh[2][0], height - nh[2][1] - 1, self.convertProbToColor(prob))

            if not self.encoder.isWall(nh[3]):
                prob = self.getProbabilityFromShieldPerDirection(state, RIGHT)
                next_state.data.addColorField(nh[3][0], height - nh[3][1] - 1, self.convertProbToColor(prob))

            self.color_counter = 1
    
    def color(self, state, next_state):
        height = state.data.layout.height
        width = state.data.layout.width
        x_pac = height - state.getPacmanPosition()[1] - 1
        y_pac = state.getPacmanPosition()[0]
        actions = ["North", "South", "East", "West", "Stop"]
        legalActions = self.getLegalActions(state)
        safeActions = self.getSafeActions(state, actions, legalActions)
        # print("Col")
        # print(x_pac, y_pac)
        # print(legalActions)
        # print(safeActions)
        # # print(pacman[0], pacman[1])
        # print(state)

        if self.color_counter == MAX_TIME_COLORED:
            self.color_counter == 0
            next_state.data.removeAllColorFields()

        if self.color_counter > 0 and self.color_counter < MAX_TIME_COLORED:
            self.color_counter += 1

        # if self.encoder.isCrossing(x_pac, y_pac):

        next_state.data.removeAllColorFields()
        # nh = self.encoder.neighborHood([x_pac, y_pac])
        walls = state.getWalls()
        print(walls)
        
        layout = np.array([list(line) for line in state.data.layout.layoutText])
        # layout = np.empty((height, width), dtype=char)
        layout[True] = '.'
        # print(layout)
        # print(layout.shape)
        walls = np.array(state.getWalls().data).T
        # print(walls.shape)
        walls = np.array([list(line) for line in walls])
        layout[walls] = '%'
        layout = np.flip(layout, axis=0)
        if x_pac<height-2 and not layout[x_pac+1][y_pac]=='%':
            prob = 0 if "South" in safeActions else 1
            next_state.data.addColorField(y_pac, height - (x_pac+1)-1, self.convertProbToColor(prob))
            
        if x_pac>0 and not layout[x_pac-1][y_pac]=='%':
            prob = 0 if "North" in safeActions else 1
            next_state.data.addColorField(y_pac, height - (x_pac-1)-1, self.convertProbToColor(prob))
            
        if y_pac>0 and not layout[x_pac][y_pac-1]=='%':
            prob = 0 if "West" in safeActions else 1
            next_state.data.addColorField(y_pac-1, height - (x_pac)-1, self.convertProbToColor(prob))

        if y_pac<width-2 and not layout[x_pac][y_pac+1]=='%':
            prob = 0 if "East" in safeActions else 1
            next_state.data.addColorField(y_pac+1, height - (x_pac)-1, self.convertProbToColor(prob))

        self.color_counter = 1


    def update(self, state, action, next_state, reward):

        if not self.localizedShield:            
            if not self.encoded:
                self.encoded=True
                self.shielder = Shield(state,self.symX,self.symY)
                self.encoder = StormEncoder(state,self.symX,self.symY)

            #use shield to dertermine safe actions
            if self.episodesSoFar > self.numGhostTraining:
                if self.shielder.getShield() !=None and not self.withoutShield:
                    #safe_actions = self.getSafeActionsFromShield(state, next_state)
                    self.colorInCrossing(state, next_state)

            if len(self.open)==0:#calculate new shield. 
                if self.episodesSoFar <= self.numGhostTraining:
                    self.updateGhostTable(state, next_state)
        else:
            if self.episodesSoFar > self.numGhostTraining:
                self.color(state, next_state)
                # if self.shielder.getShield() !=None and not self.withoutShield:
                #     #safe_actions = self.getSafeActionsFromShield(state, next_state)
                #     self.colorInCrossing(state, next_state)

        #update weights based on transition

        difference = reward + self.discount * self.getValue(next_state) - self.getQValue(state, action)

        features = self.featExtractor.getFeatures(state, action)
        for key in list(features.keys()):
            self.weights[key] = self.weights[key] + self.alpha * difference * features[key]


    # Retuns in what direction Pacman is in relation to the Ghost
    def getDirectionPacmanToGhost(self, x_ghost, y_ghost, x_pacman, y_pacman):

        dir_pacman = STOP

        if x_ghost < x_pacman and y_ghost == y_pacman:
            dir_pacman = RIGHT
        if x_ghost > x_pacman and y_ghost == y_pacman:
            dir_pacman = LEFT
        if x_ghost == x_pacman and y_ghost < y_pacman:
            dir_pacman = UP
        if x_ghost == x_pacman and y_ghost > y_pacman:
            dir_pacman = DOWN

        if x_ghost < x_pacman and y_ghost < y_pacman:
            dir_pacman = TOP_RIGHT
        if x_ghost > x_pacman and y_ghost < y_pacman:
            dir_pacman = TOP_LEFT
        if x_ghost < x_pacman and y_ghost > y_pacman:
            dir_pacman = BOTTOM_RIGHT
        if x_ghost > x_pacman and y_ghost > y_pacman:
            dir_pacman = BOTTOM_LEFT

        return dir_pacman

    def convertCardinalDirection(self, cardinal):

        if cardinal == "East":
            return RIGHT
        if cardinal == "West":
            return LEFT
        if cardinal == "South":
            return UP
        if cardinal == "North":
            return DOWN
        if cardinal == "Stop":
            return STOP

    def mapIntDirectionToString(self, direction):

        if direction == RIGHT:
            return STR_RIGHT
        if direction == LEFT:
            return STR_LEFT
        if direction == UP:
            return STR_UP
        if direction == DOWN:
            return STR_DOWN
        if direction == STOP:
            return STR_STOP
        if direction == TOP_RIGHT:
            return STR_TOP_RIGHT
        if direction == TOP_LEFT:
            return STR_TOP_LEFT
        if direction == BOTTOM_RIGHT:
            return STR_BOTTOM_RIGHT
        if direction == BOTTOM_LEFT:
            return STR_BOTTOM_LEFT


    """
     Pretty print of the Ghost Table with: 
     1. corssing ID for ghost, 
     2. direction of pacman oriented on ghost, 
     3. direction of movement of ghost
    """
    def prettyPrintGhostTable(self, table):

        # assert(len(table[0]))

        print("\**********************************************************************")
        print("\*************START GHOST TABLE****************************************")
        print("\**********************************************************************")

        for entry in table:
            corssing_id = entry[0]
            dir_cghost = self.mapIntDirectionToString(entry[1])
            positioning_pacman = self.mapIntDirectionToString(entry[2])
            dir_nghost = self.mapIntDirectionToString(entry[3])
            value = str(round(entry[4], 2))
            print("Crossing: %d, Current Direction Ghost %s, Positioning Pacman: %s, Next Direction Ghost %s, Value %s" % (corssing_id, dir_cghost, positioning_pacman, dir_nghost, value))


        print("\**********************************************************************")
        print("\*************END GHOST TABLE******************************************")
        print("\**********************************************************************")


    def normalizeGhostTable(self, table):

        result_table = []
        if len(table)  <=0:
            return result_table
        c_setting = [table[0]]
        c_signature = table[0][:3]
        c_sum = table[0][4]

        for row in table[1:]:
            signature = row[:3]

            if np.array_equal(c_signature, signature): # found entry with same signature
                c_setting.append(row)
                c_sum += row[4]

            else:   # found new signature, normalize all values
                for entry in c_setting:
                    new_entry = np.append(entry[:4], entry[4]/c_sum)
                    result_table.append(new_entry)

                c_setting = [row]
                c_signature = signature
                c_sum = row[4]

        return result_table


    def setDumpParameters(self,dump,open):
        self.open=open
        self.dump=dump

    def setSymmetryParameters(self,symX,symY):
        self.symX=symX
        self.symY=symY

    def final(self, state):
        " Called at the end of each game."
        # call the super-class final method
        PacmanQAgent.final(self, state)
        if self.shielder:
            if self.episodesSoFar==1 and len(self.open)!=0:
                print("Loading shield from file: " + self.open)
                self.shielder.loadShield(self.open)
                self.episodesSoFar=self.numGhostTraining+1
                self.shielder.prettyPrintShield()

            # done learning the model of the ghost
            if self.episodesSoFar == self.numGhostTraining:
                assert(len(self.open)==0)
                sorted_ghost_table = sorted(self.ghostTable)
                normalized_ghost_table = self.normalizeGhostTable(np.asarray(sorted_ghost_table))
                self.prettyPrintGhostTable(normalized_ghost_table)
                print("Start computation of the shield.")
                self.shielder.computeShield(state, normalized_ghost_table)

                #dump shield
                if len(self.dump)>0:
                    print("dumping current shield to file: "+self.dump)
                    self.shielder.dumpShield(self.dump)

                self.shielder.prettyPrintShield()

        # did we finish training?
        if self.episodesSoFar == self.numTraining + self.numGhostTraining:
            # you might want to print your weights here for debugging
            #print("Done with Training")
            pass
