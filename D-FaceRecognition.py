import struct
import mediapipe as mp
import time
import pyrealsense2 as rs
import numpy as np
import cv2
import csv
import os

# _*_ coding: UTF-8 _*_

# Create a data directory in the current working directory if it doesn't exist
data_dir = os.path.join(os.getcwd(), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Use relative path for data storage
csv_file_path = os.path.join(data_dir, 'face_recognition_data.csv')

pipeline = rs.pipeline()  # Define pipeline process, create a pipeline
config = rs.config()  # Define configuration
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)  # Configure depth stream
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # Configure color stream

pipe_profile = pipeline.start(config)  # Start streaming

pc = rs.pointcloud()  # Declare point cloud object
points = rs.points()


def get_images():
    frames = pipeline.wait_for_frames()  # Wait to get image frames, get color and depth frame sets
    depth_frame = frames.get_depth_frame()  # Get depth frame
    color_frame = frames.get_color_frame()  # Get color frame

    ###### Convert images to numpy arrays #####
    img_color = np.asanyarray(color_frame.get_data())  # RGB image
    img_depth = np.asanyarray(depth_frame.get_data())  # Depth image (default 16-bit)

    return img_color, img_depth, depth_frame, color_frame


def get_3d_camera_coordinate(depth_pixel, color_frame, depth_frame):
    x = depth_pixel[0]
    y = depth_pixel[1]

    ###### Calculate point cloud #####
    pc.map_to(color_frame)
    points = pc.calculate(depth_frame)
    vtx = np.asanyarray(points.get_vertices())
    vtx = np.reshape(vtx, (480, 640, -1))

    camera_coordinate = vtx[y][x][0]
    dis = camera_coordinate[2]
    return dis, camera_coordinate


# Create or overwrite CSV file and write headers
with open(csv_file_path, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    # Add headers
    csv_writer.writerow(['X', 'Y', 'Distance'])

pTime = 0

mpDraw = mp.solutions.drawing_utils  # drawing_utils module: draw feature points and bounding boxes
mpFaceMesh = mp.solutions.face_mesh
faceMesh = mpFaceMesh.FaceMesh(max_num_faces=1)  # Initialize FaceMesh module
drawSpec = mpDraw.DrawingSpec(thickness=1, circle_radius=2)  # Drawing style

data_list = []  # Used to store the last 100 data points

while True:
    img_color, img_depth, depth_frame, color_frame = get_images()
    img = img_color
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = faceMesh.process(imgRGB)  # process(): detect face keypoints

    # Get keypoint information
    if results.multi_face_landmarks:
        for faceLms in results.multi_face_landmarks:
            mpDraw.draw_landmarks(img, faceLms, mpFaceMesh.FACEMESH_TESSELATION, drawSpec, drawSpec)  # Draw keypoints
            for id, lm in enumerate(faceLms.landmark):
                ih, iw, ic = img.shape
                x, y = int(lm.x * iw), int(lm.y * ih)

                if id == 16:
                    depth_pixel = [x, y]
                    dis, camera_coordinate = get_3d_camera_coordinate(depth_pixel, color_frame, depth_frame)
                    message = [camera_coordinate[0], camera_coordinate[1], dis]
                    print(message)

                    # Add data to list
                    data_list.append(message)

                    # Only keep the latest 100 data points
                    if len(data_list) > 100:
                        data_list.pop(0)

                    # Write data to CSV file
                    with open(csv_file_path, mode='w', newline='') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(['X', 'Y', 'Distance'])  # Write headers
                        csv_writer.writerows(data_list)  # Write all data

    # Frame count
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.putText(img, f'FPS:{int(fps)}', (20, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

