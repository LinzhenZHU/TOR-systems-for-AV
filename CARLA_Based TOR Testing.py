#!/usr/bin/env python
#!/usr/bin/env python

'''
client for running scenarios

'''

#USE carla99 env

import glob
import os
import sys
import time
import pygame

import argparse
import math

from carlahelp import spawn, util
from carlahelp.filehelp import make_file_name, date_string, save_as_json, read_json_config
from core.input import DualControl
from core.sync_mode import CarlaSyncMode
from scenario_class.bike_crossing_scenario import BikeCrossing
from scenario_class.car_crash_scenario import CarCrashScenario
from scenario_class.pedestrian_crossing_scenario import PedestrianCrossing

'''
To be able to use this import please add the following environment variable: PYTHONPATH=%CARLA_ROOT%/PythonAPI/carla 
'''
# from core.custom_behaviour_agent import BehaviorAgent
from agents.navigation.behavior_agent import BehaviorAgent

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
	pass

import carla

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

from threading import Thread
FIRST_AUTOPILOT_DESTINATION = carla.Location(12.14012622833252,73.52417755126953,0.4963371157646179)
AUTOPILOT_DESTINATION = carla.Location(230.35769653320312,-367.8263244628906,0.7294923067092896)
SECOND_AUTOPILOT_DESTINATION = carla.Location(246.295654296875,-368.1007995605469,0.7278993129730225)
THIRD_AUTOPILOT_DESTINATION = carla.Location(386.3035583496094,-214.28460693359375,0.9033592939376831)
FOURTH_AUTOPILOT_DESTINATION = carla.Location(344.11126708984375,13.860794067382812,0.7798944711685181)
FIFTH_AUTOPILOT_DESTINATION = carla.Location(-72.68221282958984,9.428476333618164,10.52769660949707)


# Enable this to place the camera on dirvers view.x=388.853943, y=-185.182007, z=0.001697
DRIVERVIEW_CAMERA = True

MAIN_CAMERA_TRANSFORM = carla.Transform(carla.Location(x=1, z=1), carla.Rotation(pitch=-50, yaw=180))

if DRIVERVIEW_CAMERA == True:
    MAIN_CAMERA_TRANSFORM = carla.Transform(carla.Location(x=10.5, y=0.0, z=0.83), carla.Rotation(yaw=180, pitch=-5))

MIRROR_W = 300
MIRROR_H = 200

DISPLAY_W = 3840
DISPLAY_H = 650

SCREEN_W = DISPLAY_W
SCREEN_H = max(DISPLAY_H, MIRROR_H)

FRONT_W = 360
FRONT_H = 100

VIEW_W = DISPLAY_W
VIEW_H = max(DISPLAY_H, MIRROR_H)

FREQ = 15


def image_np(image):
    array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    array = np.reshape(array, (image.height, image.width, 4))
    array = array[:, :, :3]
    return array[:, :, ::-1]

def draw_image(surface, image, blend=False):
    array = image_np(image)
    image_surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
    if blend:
        image_surface.set_alpha(100)
    surface.blit(image_surface, (MIRROR_W, 0))

def draw_cam(surface, image, u, v, flip=True):
    array = image_np(image)
    if flip == True:
        array = np.fliplr(array)
    image_surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
    #surface.blit(image_surface,(0,DISPLAY_H-FRONT_H))
    surface.blit(image_surface,(u,v))

def get_font(font_size=16):
    fonts = [x for x in pygame.font.get_fonts()]
    default_font = 'ubuntumono'
    font = default_font if default_font in fonts else fonts[0]
    font = pygame.font.match_font(font)
    return pygame.font.Font(font, font_size)

def hlc_string(hlc):
    if hlc == 2:
        return "Follow"
    elif hlc == 3:
        return "Right Turn"
    elif hlc == 4:
        return "Left Turn"
    elif hlc == 5:
        return "Right Lane Change"
    else:
        return "Left Lane Change"

def should_quit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                return True
    return False


def main(args):
    actor_list = []
    sensor_list = []
    pygame.init()

    display = pygame.display.set_mode(
        (SCREEN_W, SCREEN_H),
        pygame.HWSURFACE | pygame.DOUBLEBUF)
    fill_rect = pygame.Rect((0,0,MIRROR_W, SCREEN_H/2))
    pygame.display.set_caption('CARLA Scenarios')
    font = pygame.font.Font('C:/Users\suxjb1\Desktop\carla-takeover-client-main/font/simsun.ttf', 18)
    font_mid = pygame.font.Font('C:/Users\suxjb1\Desktop\carla-takeover-client-main/font/simsun.ttf', 32)
    font_big = pygame.font.Font('C:/Users\suxjb1\Desktop\carla-takeover-client-main/font/simsun.ttf', 42)
    clock = pygame.time.Clock()

    client = carla.Client('localhost', 2000)
    client.set_timeout(50.0)

    world = client.get_world()
    world = client.reload_world()

    config = read_json_config(args.spawn_config)

    # This agent will drive the autopilot to certain destination
    behaviour_agent = None
    is_agent_controlled = False
    prev_agent_autopilot_enabled = False

    scenario_instance = None
    scenario_class = None

    try:
        m = world.get_map()

        sx, sy, sz = float(config['ego_actor']['x']), float(config['ego_actor']['y']), float(config['ego_actor']['z'])
        syaw, spitch, sroll = float(config['ego_actor']['yaw']), float(config['ego_actor']['pitch']), float(config['ego_actor']['roll'])
        s_loc = carla.Location(sx, sy, sz+1)
        s_rot = carla.Rotation(yaw=syaw, pitch=spitch, roll=sroll)
        start_pose = carla.Transform(location=s_loc, rotation=s_rot)

        #spawn car
        blueprint_library = world.get_blueprint_library()
        car_bp = blueprint_library.find(config['ego_actor']['actor_type'])

        #car_bp.set_attribute('color','255,20,147')
        #car_bp.set_attribute('color','158,255,0')
        car_bp.set_attribute('role_name', 'hero')
        vehicle = world.spawn_actor(
            car_bp,
            start_pose)
        #print(vehicle.attributes.get('role_name'))
        actor_list.append(vehicle)

        #spawn spectator cam
        cam_bp = blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', str(VIEW_W))
        cam_bp.set_attribute('image_size_y', str(VIEW_H))
        # cam_bp.set_attribute('sensor_tick',str(FREQ))
        camera_rgb = world.spawn_actor(
            cam_bp,
            MAIN_CAMERA_TRANSFORM,
            attach_to=vehicle,
            attachment_type=carla.AttachmentType.SpringArm)

        # every sensor must be registered by
        # appending to actor list AND sensor list
        actor_list.append(camera_rgb)
        sensor_list.append(camera_rgb)

        # rearview cam
        # camera_front = spawn.spawn_rgb(vehicle, world, img_x=FRONT_W, img_y=FRONT_H, hz=FREQ, pitch=-12)
        cam_bp.set_attribute('image_size_x', str(FRONT_W))
        cam_bp.set_attribute('image_size_y', str(FRONT_H))
        cam_bp.set_attribute('fov', str(60))
        mirror_rear = world.spawn_actor(
            cam_bp,
            carla.Transform(carla.Location(x=-2, z=1.3), carla.Rotation(yaw=-180)),
            attach_to=vehicle)
        actor_list.append(mirror_rear)
        sensor_list.append(mirror_rear)

        # spawn left mirror
        cam_bp.set_attribute('image_size_x', str(MIRROR_W))
        cam_bp.set_attribute('image_size_y', str(MIRROR_H))
        cam_bp.set_attribute('fov', str(70))

        mirror_left = world.spawn_actor(
            cam_bp,
            carla.Transform(carla.Location(y=-1.1, z=1.0), carla.Rotation(yaw=-160)),
            attach_to=vehicle)

        # every sensor must be registered by
        # appending to actor list AND sensor list
        actor_list.append(mirror_left)
        sensor_list.append(mirror_left)

        # spawn right mirror
        cam_bp.set_attribute('image_size_x', str(MIRROR_W))
        cam_bp.set_attribute('image_size_y', str(MIRROR_H))
        cam_bp.set_attribute('fov', str(70))
        mirror_right = world.spawn_actor(
            cam_bp,
            carla.Transform(carla.Location(y=1.2, z=1.0), carla.Rotation(yaw=160)),
            attach_to=vehicle)

        # every sensor must be registered by
        # appending to actor list AND sensor list
        actor_list.append(mirror_right)
        sensor_list.append(mirror_right)



        world.player = vehicle
        controller = DualControl(vehicle, world=world, start_in_autopilot=False, agent_controlled=True)

        global wheel_icon
        wheel_icon = pygame.image.load('assets/icons/youzhuanwandeng.gif').convert_alpha()
        wheel_icon_2 = pygame.image.load('assets/icons/white.gif').convert_alpha()


        #initial scenario stage
        flash_on = False

        #initial hlc
        hlc = 2

        if DRIVERVIEW_CAMERA == True:
            camera_rgb.set_transform(MAIN_CAMERA_TRANSFORM)

        # Create a synchronous mode context.
        #SENSORS SHOULD BE PASSED IN THE SAME ORDER AS IN ACTOR_LIST
        with CarlaSyncMode(world, vehicle, m, *sensor_list, fps=FREQ, record=args.record, scenario=args.scenario) as sync_mode:

            record_start_flag = False
            yaw_prev = None

            import time
            start_time = 0
            j = 0
            i = 0
            voice = 0
            k = 0
            s = 1
            t = 0
            ta = 0
            counter = 60
            counter_a=20
            t0 = 0

            while True:


                if should_quit():
                    return

                #print(sync_mode._queues)
                clock.tick()

                # Advance the simulation and wait for the data.
                tick_data = sync_mode.tick(timeout=10.0, hlc=hlc)
                snapshot = tick_data[0]
                image_rgb = tick_data[1]

                image_front = tick_data[2]
                image_mirror_left = tick_data[3]
                image_mirror_right = tick_data[4]


                #parse for control input and run vehicle
                hlc = controller.parse_events(vehicle, clock)
                control_states = vehicle.get_control()

                #draw trail based on hlc
                #sync_mode.draw_trail(hlc)

                v = vehicle.get_velocity()
                trans = vehicle.get_transform()
                #print('{:.3f}, {:.3f}'.format(trans.location.x, trans.location.y))

                
                closest_wp = m.get_waypoint(trans.location)
                draw_loc = closest_wp.transform.location+carla.Location(z=2)
                #sync_mode.world.debug.draw_point(draw_loc, life_time=0.05)
                #print(closest_wp.is_junction, len(closest_wp.next(0.5)))

                #track SECOND waypoint in queue as first does not shift with lc command
                second_wp = sync_mode.waypoint_queue[1]
                heading_error = second_wp.transform.rotation.yaw - trans.rotation.yaw
                heading_error = util.angle_wrap(heading_error)
                delta_x, delta_y = util.car_frame_deltas(trans, second_wp.transform.location)

                vx, vy = util.measure_forward_velocity(v, trans.rotation, return_both=True)
                vx_kph = vx*3.6
                curvature = util.curvature(sync_mode.waypoint_queue[1].transform, sync_mode.waypoint_queue[2].transform)

                #lateral accel
                #r = 1/(curvature + 1e-6)
                #print(vx**2/r)

                if len(sync_mode.vehicles_close)>0:
                    #print(sync_mode.vehicles_close[0][0], sync_mode.vehicles_close[0][1].__str__())
                    dist_to_car = max(sync_mode.vehicles_close[0][0] - 4.5, 0)
                else:
                    dist_to_car = 50.0

                if len(sync_mode.pedestrians_close)>0:
                    #print(sync_mode.vehicles_close[0][0], sync_mode.vehicles_close[0][1].__str__())
                    dist_to_walker = max(sync_mode.pedestrians_close[0][0] - 4.5, 0)
                else:
                    dist_to_walker = 50.0

                affordance = (heading_error, delta_y, curvature, dist_to_car, dist_to_walker)
                #
                # if voice == 0:
                #     pygame.mixer.music.load('assets/sounds/driving.mp3')
                #     pygame.mixer.music.play(1, 0)
                #     voice = 1


                '''
                VOICE GUIDANCE BEGIN
                '''

                location = trans.location

                if controller._agent_autopilot_enabled == False:
                    stage = "manual mode"

                    if abs(location.x - 24.250972747802734) < 20 and abs(
                            location.y - 10.021620750427246) < 20 and k == 0 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/right_sideway.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x + 14.52480411529541) < 20 and abs(
                            location.y + 62.76133346557617) < 20 and k == 1 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/keep_straight2.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x + 15.65413761138916) < 20 and abs(
                            location.y - 51.47540283203125) < 20 and k == 2 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/destination.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x - 15.075854301452637) < 20 and abs(
                            location.y - 36.76966094970703) < 20 and k == 3 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/right_sideway.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x - 17.43956184387207) < 20 and abs(
                            location.y - 106.27178192138672) < 20 and k == 4 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/keep_straight2.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x - 15.722091674804688) < 20 and abs(
                            location.y + 46.04341125488281) < 20 and k == 5 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/destination.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x - 24.250972747802734) < 15 and abs(
                            location.y - 10.021620750427246) < 15 and k == 6 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/right_sideway.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x + 14.52480411529541) < 20 and abs(
                            location.y + 62.76133346557617) < 20 and k == 7 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/keep_straight2.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1

                    if abs(location.x + 15.524093627929688) < 20 and abs(
                            location.y - 69.8696060180664) < 20 and k == 8 and i > 0:
                        # pygame.mixer.music.load('assets/sounds/destination.mp3')
                        # pygame.mixer.music.play(1, 0)
                        k = k + 1








                '''         
                VOICE GUIDANCE END
                '''


                '''
                behaviour agent begin
                '''

                if vx > 0.01:
                    record_start_flag = True
                if sync_mode.record and record_start_flag:
                    #sync_mode.record_image(tick_data[1:])
                    sync_mode.record_frame(snapshot, trans, v, control_states, affordance, second_wp, hlc, stage)

                #image_semseg.convert(carla.ColorConverter.CityScapesPalette)
                fps = round(1.0 / snapshot.timestamp.delta_seconds)

                # Draw the display.
                display.fill((0, 0, 0), rect=fill_rect)
                # draw_image(display, image_rgb)
                draw_cam(display, image_rgb, 0, 0, False)
                draw_cam(display, image_front, (DISPLAY_W/2 + 200), 0)
                draw_cam(display, image_mirror_left, 0, SCREEN_H-300)
                draw_cam(display, image_mirror_right, DISPLAY_W - MIRROR_W, SCREEN_H-300)




                if controller._agent_autopilot_enabled == True:

                    if j == 1:
                        if t == 0:
                            t0 = pygame.time.get_ticks()
                            t = t + 1
                        if pygame.time.get_ticks() - t0 > 1000:
                            counter = counter - 1
                            t0 = pygame.time.get_ticks()
                        # display.blit(
                        #     font_big.render(u'%ss 后将驶离自动驾驶路段' % counter, True, (255, 255, 255)),
                        #     (SCREEN_W // 2 - 150, SCREEN_H // 2 + 60))


                    if j == 2 or j == 3:
                        if ta == 0:
                            ta0 = pygame.time.get_ticks()
                            ta = ta + 1
                        if pygame.time.get_ticks() - ta0 > 1000:
                            counter_a = counter_a - 1
                            ta0 = pygame.time.get_ticks()
                        # display.blit(
                        #      font_big.render(u'请接管 %ss' % counter_a, True, (255, 0, 0)),
                        #      (SCREEN_W // 2 - 40, SCREEN_H // 2 - 70))
                        display.blit(wheel_icon, (SCREEN_W // 2-10, SCREEN_H // 2 - 10))


                if controller._agent_autopilot_enabled == True:
                    if prev_agent_autopilot_enabled == False:
                        if s == 1:
                            stage = "autonomous driving"
                            s=s+1
                            print(s, stage)
                            # Init the agent
                        behaviour_agent = BehaviorAgent(vehicle, ignore_traffic_light=False, behavior="aggressive")
                        # Set agent's destination
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), FIRST_AUTOPILOT_DESTINATION, clean=True)
                        print ("Autopilot is controlled by BehaviourAgent to destination: {}".format(FIRST_AUTOPILOT_DESTINATION))
                        print ("Autopilot start at:", behaviour_agent.vehicle.get_location())
                        # pygame.mixer.music.load('assets/sounds/engine_start.mp3')
                        # pygame.mixer.music.play(1, 0)

                    behaviour_agent.update_information()

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 0 and i == 0: # For destination precision change this value
                        print("First Target almost reached")
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), AUTOPILOT_DESTINATION, clean=True)
                        behaviour_agent.update_information()
                        i = i + 1
                        print (i)

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 58 and j == 0 and i == 1:  # For destination precision change this value
                        j = j + 1
                        print(j)
                        if s == 2:
                            stage = "prepare to takeover"
                            s=s+1
                        # pygame.mixer.music.load('assets/sounds/pre_alert.mp3')
                        # pygame.mixer.music.play(1, 0)

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 0 and i == 1: # For destination precision change this value
                        print("First Target almost reached")
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), SECOND_AUTOPILOT_DESTINATION, clean=True)
                        behaviour_agent.update_information()
                        i = i + 1
                        print (i)

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 0 and i == 2: # For destination precision change this value
                        print("First Target almost reached")
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), THIRD_AUTOPILOT_DESTINATION, clean=True)
                        behaviour_agent.update_information()
                        i = i + 1
                        print (i)



                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 0 and i == 3: # For destination precision change this value
                        print("First Target almost reached")
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), FOURTH_AUTOPILOT_DESTINATION, clean=True)
                        behaviour_agent.update_information()
                        i = i + 1
                        print (i)

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 0 and i == 4: # For destination precision change this value
                        print("Second Target almost reached")
                        behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), FIFTH_AUTOPILOT_DESTINATION , clean=True)
                        behaviour_agent.update_information()
                        i = i + 1
                        print (i)

                    if counter == 0 and j == 1: # For destination precision change this value
                        j = j + 1
                        print(j)
                        if s == 3:
                            stage = "takeover now"
                            s=s+1
                        pygame.mixer.music.load('assets/sounds/haptictrigger.mp3')
                        pygame.mixer.music.play(1, 0)

                    if counter_a == 10 and i == 5 and j == 2: # For destination precision change this value
                        j = j + 1
                        i = i + 1
                        print(j)
                        if s == 4:
                            stage = "request upgraded"
                            s=s+1
                        behaviour_agent.update_information()
                        # pygame.mixer.music.load('assets/sounds/bell.mp3')
                        # pygame.mixer.music.play(1, 0)


                    if counter_a == 1 and j == 3: # For destination precision change this value
                        # pygame.mixer.music.load('assets/sounds/pullover.mp3')
                        # pygame.mixer.music.play(1, 0)
                        if s == 5:
                            stage = "emergency stop"
                            s=s+1
                        j = j + 1
                        print(j, i)

                    if len(behaviour_agent.get_local_planner().waypoints_queue) <= 5 and i == 5:  # For destination precision change this value
                        v = vehicle.get_velocity()
                        behaviour_agent.update_information()

                        if abs(vy) > 1 or abs(vx) > 1:
                            behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(), behaviour_agent.vehicle.get_location(), clean=True)
                            vc = carla.VehicleControl(throttle=0, steer=0, brake=0.5)
                            sync_mode.car.apply_control(vc)
                        else:
                            i = i + 1
                            if s == 3:
                                stage = "auto off"
                                s = 1
                            controller._agent_autopilot_enabled = False
                            behaviour_agent.set_destination(behaviour_agent.vehicle.get_location(),
                                                            behaviour_agent.vehicle.get_location(), clean=True)
                            behaviour_agent.update_information()


                    else:
                        input_control = behaviour_agent.run_step()
                        world.player.apply_control(input_control)

                prev_agent_autopilot_enabled = controller._agent_autopilot_enabled
                '''
                behaviour agent end
                '''

                #record
                display.blit(
                    font.render('方向：%2d' % control_states.gear, False, (255, 125, 255)),
                    (SCREEN_W * 0.4 - 100, SCREEN_H - 100))

                display.blit(
                    font_mid.render('速度:% 2d km/h' % vx_kph, False, (255, 255, 255)),
                    (SCREEN_W * 0.4 - 100, SCREEN_H - 180))

                autopilot_str_val = 'OFF'
                if controller._agent_autopilot_enabled == True:
                    autopilot_str_val = 'ON'
                display.blit(
                    font.render('自动:' + autopilot_str_val, False, (255, 125, 255)),
                    (SCREEN_W * 0.4 - 100, SCREEN_H - 120))
                pygame.display.flip()

    except Exception as exception:
        print (str(exception))

    finally:
        print('destroying actors not done.')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--record', type=bool, default=False)
    parser.add_argument('-s', '--scenario', type=bool, default=False)
    parser.add_argument('-sp', '--spawn_config', type=str, default='')
    parser.add_argument('-sc', '--scenario_config', type=str, default='')
    args = parser.parse_args()

    try:

        main(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
