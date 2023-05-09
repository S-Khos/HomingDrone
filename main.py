# todo
# - put tracker in seperate thread to minimize fps loss
# - implement auto flight control (homing)
# - implment manual flight control

from djitellopy import Tello
import cv2, math, time, threading
import numpy as np

init_alt = 0
relative_alt = 0
spd_mag = 0

width = 960
height = 720
font = cv2.FONT_HERSHEY_DUPLEX
font_scale = .6
red = (0, 0, 255)
green = (0, 255, 0)
blue = (255, 0, 0)
white = (255, 255, 255)
black = (0, 0, 0)
line_type = 1
manual_control = True

tracker = None
tracking = False
bbox = None
first_pointB = False
second_pointB = False
first_point = (0, 0)
second_point = (0, 0)
point_counter = 0


tello = Tello()
tello.connect()
tello.streamon()
init_alt = tello.get_barometer()

try:
    frame_read = tello.get_frame_read()
except:
    print("[FEED] - No Feed Signal")


# Mouse callback function
def onMouse(event, x, y, flags, param):
    global tracker, tracking, bbox, point_counter, first_point, second_point

    if event == cv2.EVENT_LBUTTONDOWN:
        
        if point_counter == 0:
            print("first point set to ", x, y)
            first_point = (x, y)
            
        if point_counter == 1:
            print("second point set to ", x, y)
            second_point = (x, y)
        
        point_counter += 1
        
        if tracking and point_counter == 3:
            point_counter = 0
            tracking = False
            print("reset")

        if point_counter == 2:
            bbox = (first_point[0], first_point[1], second_point[0], second_point[1])
            tracker = cv2.legacy.TrackerCSRT_create()
            tracker.init(empty_frame, bbox)
            tracking = True
            

cv2.namedWindow("FEED", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("FEED", onMouse)


while True:
    try:
        frame = frame_read.frame
        empty_frame = frame.copy()
        empty_frame = cv2.cvtColor(empty_frame, cv2.COLOR_BGR2RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        relative_alt = (tello.get_barometer() - init_alt) * 0.0328
        spd_mag = int(math.sqrt(tello.get_speed_x() ** 2 + tello.get_speed_y() ** 2 + tello.get_speed_z() ** 2))

        # top left
        cv2.putText(frame, "BAT   {}%".format(tello.get_battery()), (5, 25), font, font_scale, white, line_type)
        cv2.putText(frame, "TEMP  {} C".format(tello.get_temperature()), (5, 55), font, font_scale, white, line_type)

        # crosshair
        cv2.line(frame, (int(width / 2) - 30, int(height / 2)), (int(width / 2) - 10, int(height / 2)), white, 1)
        cv2.line(frame, (int(width / 2) + 30, int(height / 2)), (int(width / 2) + 10, int(height / 2)), white, 1)
        cv2.line(frame, (int(width / 2), int(height / 2) - 30), (int(width / 2), int(height / 2) - 10), white, 1)
        cv2.line(frame, (int(width / 2), int(height / 2) + 30), (int(width / 2), int(height / 2) + 10), white, 1)

        #crosshair stats
        spd_size = cv2.getTextSize("SPD  0", font, font_scale, line_type)[0][0]
        cv2.putText(frame, "SPD  {}".format(abs(spd_mag)), ((width // 2) - 90 - spd_size, (height // 2) - 100), font, font_scale, white, line_type)
        cv2.putText(frame, "ALT  {:.1f} FT".format(relative_alt), ((width // 2) + 90, (height // 2) - 100), font, font_scale, white, line_type)

        # bottom left telemtry
        cv2.putText(frame, "SPD  {}  {}  {}".format(tello.get_speed_x(), tello.get_speed_y(), tello.get_speed_z()), (5, height - 70), font, font_scale, white, line_type)
        cv2.putText(frame, "ACC  {}  {}  {}".format(tello.get_acceleration_x(), tello.get_acceleration_y(), tello.get_acceleration_z()), (5, height - 40), font, font_scale, white, line_type)
        cv2.putText(frame, "YPR  {}  {}  {}".format(tello.get_pitch(), tello.get_roll(), tello.get_height()), (5, height - 10), font, font_scale, white, line_type)

        # top right
        time_size = cv2.getTextSize("T + {}".format(tello.get_flight_time()), font, font_scale, line_type)[0][0]
        cv2.putText(frame, "T + {}".format(tello.get_flight_time()), (width - time_size, 25), font, font_scale, white, line_type)

        # top center
        if (manual_control):
            
            cv2.rectangle(frame, (width//2 - 20, 10), (width//2 + 30, 28), white, -1)
            cv2.putText(frame, "MANL", (width//2 - 20, 25), font, font_scale, black, line_type)

        else:

            cv2.rectangle(frame, (width//2 - 20, 10), (width//2 + 30, 28), white, -1)
            cv2.putText(frame, "AUTO", (width//2 - 20, 25), font, font_scale, black, line_type)

        if tracking:
            lock_size = cv2.getTextSize("LOCK", font, font_scale, line_type)[0][0]
            cv2.rectangle(frame, (width//2 - (lock_size // 2), height - 38), (width//2 + lock_size - 25, height - 20), white, -1)
            cv2.putText(frame, "LOCK", (width//2 - (lock_size // 2), height - 23), font, font_scale, black, line_type)


        if tracking:
            ret, bbox = tracker.update(empty_frame)

            if ret:
                # Draw the tracked object on the frame
                x, y, w, h = [int(value) for value in bbox]
                # top left
                cv2.line(frame, (x, y), (x + 50, y), white, 1)
                cv2.line(frame, (x, y), (x, y + 50), white, 1)
                # top right
                cv2.line(frame, (x + w, y), (x + w - 50, y), white, 1)
                cv2.line(frame, (x + w, y), (x + w, y + 50), white, 1)
                # bottom left
                cv2.line(frame, (x, y + h), (x + 50, y + h), white, 1)
                cv2.line(frame, (x, y + h), (x, y + h - 50), white, 1)
                # bottom right
                cv2.line(frame, (x + w, y + h), (x + w - 50, y + h), white, 1)
                cv2.line(frame, (x + w, y + h), (x + w, y + h - 50), white, 1)

            else:

                tracking = False

    except:
        print("[FEED] - UI Error")

    try:
        cv2.imshow("FEED", frame)
    except:
        tello.streamoff()
        tello.end()

    if (cv2.waitKey(1) & 0xff) == 27:
        break

cv2.destroyAllWindows()
tello.streamoff()
tello.end()
