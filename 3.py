from __future__ import print_function
# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------



from builtins import range
import sys
import os
import random
import time
import uuid
#from PIL import Image
import json
import math

# Allow MalmoPython to be imported both from an installed
# malmo module and (as an override) separately as a native library.
try:
    import MalmoPython
    import malmoutils
except ImportError:
    import malmo.MalmoPython as MalmoPython
    import malmo.malmoutils as malmoutils


class MissionTimeoutException(Exception):
    pass


def restart_minecraft(world_state, agent_host, client_info, message):
    """"Attempt to quit mission if running and kill the client"""
    if world_state.is_mission_running:
        agent_host.sendCommand("quit")
        time.sleep(10)
    agent_host.killClient(client_info)
    raise MissionTimeoutException(message)


def run(argv=['']):
    if "MALMO_XSD_PATH" not in os.environ:
        print("Please set the MALMO_XSD_PATH environment variable.")
        return
    #forceReset="true"
    missionXML='''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            
              <About>
                <Summary>Hello world!</Summary>
              </About>
              
              <ServerSection>
                <ServerHandlers>
                  <DefaultWorldGenerator forceReset="true" />
                  <ServerQuitFromTimeUp timeLimitMs="30000"/>
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>
              
              
              <AgentSection mode="Survival">
                <Name>MalmoTutorialBot</Name>
                <AgentStart>
                    <Inventory>
                        <InventoryItem slot="8" type="diamond_pickaxe"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ObservationFromFullStats/>
                    <ObservationFromGrid>
                        <Grid name="all_the_blocks" >
                            <min x="-1" y="-1" z="-1"/>
                            <max x="1" y="2" z="1"/>
                        </Grid>
                    </ObservationFromGrid>
                    <ContinuousMovementCommands turnSpeedDegs="180"/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''

    malmoutils.fix_print()

    #agent_host = MalmoPython.AgentHost()
    agent_host = MalmoPython.AgentHost()
    malmoutils.parse_command_line(agent_host, argv)

    my_mission = MalmoPython.MissionSpec(missionXML, True)
    my_mission.timeLimitInSeconds( 300 )
    my_mission.requestVideo( 640, 480 )
    
    #my_mission.rewardForReachingPosition( 19.5, 0.0, 19.5, 100.0, 1.1 )
    

    my_mission_record = malmoutils.get_default_recording_object(agent_host, "saved_data")

    # client_info = MalmoPython.ClientInfo('localhost', 10000)
    client_info = MalmoPython.ClientInfo('127.0.0.1', 10000)
    pool = MalmoPython.ClientPool()
    pool.add(client_info)

    experiment_id = str(uuid.uuid1())
    print("experiment id " + experiment_id)

    max_retries = 3
    max_response_time = 60  # seconds

    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, pool, my_mission_record, 0, experiment_id)
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission:",e)
                exit(1)
            else:
                time.sleep(2)

    print("Waiting for the mission to start", end=' ')
    start_time = time.time()
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        print(".", end="")
        time.sleep(0.1)
        if time.time() - start_time > max_response_time:
            print("Max delay exceeded for mission to begin")
            restart_minecraft(world_state, agent_host, client_info, "begin mission")
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)
    print()

    last_delta = time.time()


    
    # main loop:
    #agent_host.sendCommand( "jump 1")
    TURN = 0
    TURN2 = 0
    JUMP = 0
    while world_state.is_mission_running:
        print("New Iteration")
        
        if JUMP > 0:
            JUMP = JUMP - 1
        if JUMP == 0:
            agent_host.sendCommand( "jump 0" )
            JUMP = JUMP - 1
        agent_host.sendCommand( "move 1" )
        if math.sin(TURN)/3 >= 0:
            agent_host.sendCommand( "turn 0.15")
        else:
            agent_host.sendCommand( "turn -0.2")
        print(TURN," ",math.sin(TURN))
        TURN = TURN + 0.3

        #agent_host.sendCommand( "jump 1" )
        time.sleep(0.5)
        world_state = agent_host.getWorldState()
        y = json.loads(world_state.observations[-1].text)
        
        #print(y["all_the_blocks"])
        dir = ""
        if y["Yaw"] + 180 < 90:
            dir="S"
            print("Facing South")
        elif y["Yaw"] < 180:
            dir="W"
            print("Facing West")
        elif y["Yaw"] < 270:
            dir="N"
            print("Facing North")
        else:
            dir="E"
            print("Facing East")

        blocks = [[],[],[],[]]
        i=0
        for x in y["all_the_blocks"]:
            blocks[math.floor(i/9)].append(x)
            i = i+1

        
        


        if dir=="S":
            willjump = False
            
            for j in range(0,3):
                if blocks[1][j] !="air":
                    willjump = True
                print(j,blocks[1][j],willjump)
            if willjump :
                JUMP = 2
                agent_host.sendCommand( "jump 1" )
        elif dir=="W":
            willjump = False
            
            for j in range(0,3):
                if blocks[1][j*3] !="air":
                    willjump = True
                print(j*3,blocks[1][j*3],willjump)
            if willjump :
                JUMP = 2
                agent_host.sendCommand( "jump 1" )
        elif dir=="E":
            willjump = False
            
            for j in range(1,4):
                if blocks[1][j*3-1] !="air":
                    willjump = True
                print(j*3-1,blocks[1][j*3-1],willjump)
            if willjump :
                JUMP = 2
                agent_host.sendCommand( "jump 1" )
        elif dir=="N":
            willjump = False
            
            for j in range(0,3):
                if blocks[1][j] !="air":
                    willjump = True
                print(j,blocks[1][j+6],willjump)
            if willjump :
                JUMP = 2
                agent_host.sendCommand( "jump 1" )

        if (blocks[1][2] !="air" and blocks[2][2] !="air" or blocks[1][4] !="air" and blocks[2][4] !="air" or
            blocks[1][2] !="air" and blocks[2][2] !="air" or blocks[1][4] !="air" and blocks[2][4] !="air"):
            TURN2 = 2

        if TURN2 >= 0:
            agent_host.sendCommand( "turn 1" )
            TURN2 = TURN2 - 1
        

        '''if blocks[1][5] != "air" or  blocks[1][5] != "grass" or blocks[1][5] != "tallgrass" :
            JUMP = 2
            agent_host.sendCommand( "jump 1" )
            print()
            print(blocks[1][5])'''

        #print(len(blocks))
        #print(blocks)

        if (world_state.number_of_video_frames_since_last_state > 0 or
           world_state.number_of_observations_since_last_state > 0 or
           world_state.number_of_rewards_since_last_state > 0):
            last_delta = time.time()
        else:
            if time.time() - last_delta > max_response_time:
                print("Max delay exceeded for world state change")
                restart_minecraft(world_state, agent_host, client_info, "world state change")
        for reward in world_state.rewards:
            print("Summed reward:",reward.getValue())
        for error in world_state.errors:
            print("Error:",error.text)
        for frame in world_state.video_frames:
            print()
            #print("Frame:",frame.width,'x',frame.height,':',frame.channels,'channels')
            #image = Image.frombytes('RGB', (frame.width, frame.height), bytes(frame.pixels) ) # to convert to a PIL image
    print("Mission has stopped.")


if __name__ == "__main__":
    run(sys.argv)
