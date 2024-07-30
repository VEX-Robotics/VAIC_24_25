# Import necessary libraries
import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os

from V5MapPosition import MapPosition

import V5Comm
from V5Comm import V5SerialComms
from V5Position import Position
from V5Position import V5GPS
from V5Web import V5WebData
from V5Web import Statistics

from model import Model, rawDetection


class Camera:
    # Class handles Camera object instantiation and data requests.
    def __init__(self):
        self.pipeline = rs.pipeline()  # Initialize RealSense pipeline
        self.config = rs.config()
        # Enable depth stream at 640x480 in z16 encoding at 30fps
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        # Enable color stream at 640x480 in rgb8 encoding at 30fps
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

    def start(self):
        self.profile = self.pipeline.start(self.config)  # Start the pipeline
        # Obtain depth sensor and calculate depth scale
        depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()

    def get_frames(self):
        return self.pipeline.wait_for_frames()  # Wait and fetch frames from the pipeline

    def stop(self):
        self.pipeline.stop()  # Stop the pipeline when finished


class Processing:
    # Class to handle camera data processing, preparing for inference, and running inference on camera image.
    def __init__(self, depth_scale):
        self.depth_scale = depth_scale
        self.align_to = rs.stream.color
        self.align = rs.align(self.align_to)  # Align depth frames to color stream
        self.model = Model()  # Initialize the object detection model
        self.HUE = 0
        self.SATURATION = 0
        self.VALUE = 0

    def process_image(self, image):
        # Enhances the image by shifting the hue and adjusting saturation and brightness.

        # Convert the image to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Modify the hue, saturation, and value channels
        hsv[..., 0] = hsv[..., 0] + self.HUE
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.SATURATION, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * self.VALUE, 0, 255)

        # Convert the image back to RGB color space for inferencing
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def updateHSV(self, newHSV):
        self.HUE = newHSV.h

        if (self.SATURATION >= 0):
            self.SATURATION = 1 + (newHSV.s) / 100
        else:
            self.SATURATION = (100 - abs(newHSV.s)) / 100

        if (self.VALUE >= 0):
            self.VALUE = 1 + (newHSV.v) / 100
        else:
            self.VALUE = (100 - abs(newHSV.v)) / 100

    def get_depth(self, detection: rawDetection, depth_img):
        # Compute the bounding box indices for the detection
        height = detection.Height
        width = detection.Width

        # If the detection is a mobile goal, look at the bottom 10 percent for better accuracy
        if detection.ClassID == 0:
            low_limit_y = 95
            high_limit_y = 100
            low_limit_x = 20
            high_limit_x = 80
        # Otherwise use the middle 10 percent
        else:
            low_limit_y = 45
            high_limit_y = 55
            low_limit_x = 45
            high_limit_x = 55
        # Calculate the indices of 10% of the detection.
        top = int(detection.y) + height * low_limit_y // 100
        bottom = int(detection.y) + height * high_limit_y // 100
        left = int(detection.x) + width * low_limit_x // 100
        right = int(detection.x) + width * high_limit_x // 100

        # Extract depth values and scale them
        depth_img = depth_img[top:bottom, left:right].astype(float)
        depth_img = depth_img * self.depth_scale
        # Filter non-zero depth values
        depth_img = depth_img[depth_img != 0]
        # Compute and return mean depth value
        meanDepth = np.nanmean(depth_img)
        return meanDepth

    def align_frames(self, frames):
        # Align depth frames to color frames
        aligned_frames = self.align.process(frames)
        # Get the aligned frames and validate them
        self.depth_frame_aligned = aligned_frames.get_depth_frame()
        self.color_frame_aligned = aligned_frames.get_color_frame()

        if not self.depth_frame_aligned or not self.color_frame_aligned:
            self.depth_frame_aligned = None
            self.color_frame_aligned = None

    def process_frames(self, frames):
        # Align frames and extract color and depth images
        # Apply a color map to the depth image
        self.align_frames(frames)
        depth_image = np.asanyarray(self.depth_frame_aligned.get_data())
        color_image = np.asanyarray(self.color_frame_aligned.get_data())
        # apply color correction to image
        color_image = self.process_image(color_image)
        depthImage = cv2.normalize(depth_image, None, alpha=0.01, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        depth_map = cv2.applyColorMap(depthImage, cv2.COLORMAP_JET)

        return depth_image, color_image, depth_map

    def detect_objects(self, color_image):
        # Perform object detection and return results using the Model class in model.py
        output, detections = self.model.inference(color_image)
        return output, detections

    def compute_detections(self, v5, detections, depth_image):
        # Create AIRecord and compute detections with depth and image data.
        # Each AIRecord contains the ClassID, Probablity, and depth information for each detection
        # In addition to the detection's camera image and map position information.
        aiRecord = V5Comm.AIRecord(v5.get_v5Pos(), [])
        for detection in detections:
            depth = self.get_depth(detection, depth_image)
            imageDet = V5Comm.ImageDetection(
                int(detection.x),
                int(detection.y),
                int(detection.Width),
                int(detection.Height),
            )
            mapPos = v5.v5Map.computeMapLocation(detection, depth, aiRecord.position)
            mapDet = V5Comm.MapDetection(mapPos[0], mapPos[1], mapPos[2])
            detect = V5Comm.Detection(
                int(detection.ClassID),
                float(detection.Prob),
                float(depth),
                imageDet,
                mapDet,
            )
            aiRecord.detections.append(detect)
        return aiRecord


class Rendering:
    # Class to handle rendering camera data and process stat data to the webserver.
    def __init__(self, web_data):
        self.web_data = web_data

    def set_images(self, output, depth_image):
        # Update web data with color and depth images
        self.web_data.setColorImage(output)
        self.web_data.setDepthImage(depth_image)

    def set_detection_data(self, aiRecord):
        # Update web data with detection information
        self.web_data.setDetectionData(aiRecord)
    
    def set_stats(self, stats, v5Pos, start_time, invoke_time, run_time):
        # Set the statistics for FPS, invoke time, run time, and CPU temp
        stats.fps = 1.0 / (time.time() - start_time)
        stats.gpsConnected = v5Pos.isConnected()
        stats.invokeTime = invoke_time
        stats.runTime = time.time() - run_time
        temp_str = os.popen("cat /sys/devices/virtual/thermal/thermal_zone1/temp").read().rstrip("\n")
        temp = float(temp_str) / 1000
        stats.cpuTemp = temp
        self.web_data.setStatistics(stats)

    def display_output(self, output):
        # Display the output image in a window
        # Handle window closing with 'q' or 'esc' keys
        cv2.namedWindow("VEX HighStakes", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("VEX HighStakes", output)
        key = cv2.waitKey(1)
        if key & 0xFF == ord("q") or key == 27:
            cv2.destroyAllWindows()


class MainApp:
    def __init__(self):
        # Initialize various components including camera, processing, and rendering
        print("Starting Initialization...")
        self.camera = Camera()
        self.camera.start()
        self.processing = Processing(self.camera.depth_scale)

        self.v5 = V5SerialComms()
        self.v5Map = MapPosition()
        self.v5Pos = V5GPS()
        self.v5Web = V5WebData(self.v5Map, self.v5Pos, self.processing)
        self.stats = Statistics(0, 0, 0, 640, 480, 0, False)
        self.rendering = Rendering(self.v5Web)

        time.sleep(1)
        print("Initialized")

    def get_v5Pos(self):
        # Return V5Position object if GPS is connected but default values if not connected
        if self.v5Pos is None:
            return Position(0, 0, 0, 0, 0, 0, 0, 0)
        return self.v5Pos.getPosition()

    def set_v5(self, aiRecord):
        # Set detection data to the Brain if it is connected but does not set any data if None
        if self.v5 is not None:
            self.v5.setDetectionData(aiRecord)

    def run(self):
        # Start main loop: capture frames, process, detect objects, compute detections, render and display
        self.v5.start()
        self.v5Pos.start()
        self.v5Web.start()
        run_time = time.time()
        print("\nStarting Loop")
        try:
            while True:
                start_time = time.time()  # start time of the loop
                frames = self.camera.get_frames()
                depth_image, color_image, depth_map = self.processing.process_frames(frames)
                invoke_time = time.time()
                output, detections = self.processing.detect_objects(color_image)
                invoke_time = time.time() - invoke_time
                aiRecord = self.processing.compute_detections(self, detections, depth_image)
                self.set_v5(aiRecord)
                self.rendering.set_images(output, depth_map)
                self.rendering.set_detection_data(aiRecord)
                self.rendering.set_stats(self.stats, self.v5Pos, start_time, invoke_time, run_time)
                # self.rendering.display_output(output)
        finally:
            self.camera.stop()


if __name__ == "__main__":
    app = MainApp()  # Create the main application
    app.run()  # Run the application
