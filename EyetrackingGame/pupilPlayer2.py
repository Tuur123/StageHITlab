import zmq
from msgpack import loads
import threading

class GetCoordsPLayer2:

    def __init__(self) -> None:
        
        self.surface_name = "screen"
        self.context = zmq.Context()

        self.x_ref = self.y_ref = 0

        # open a req port to talk to pupil
        addr = "127.0.0.1"  # remote ip or localhost
        req_port = "50021"  # same as in the pupil remote gui
        req = self.context.socket(zmq.REQ)
        req.connect("tcp://{}:{}".format(addr, req_port))

        # ask for the sub port
        req.send_string("SUB_PORT")
        sub_port = req.recv_string()

        # open a sub port to listen to pupil
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect("tcp://{}:{}".format(addr, sub_port))
        self.sub.setsockopt_string(zmq.SUBSCRIBE, f"surfaces.{self.surface_name}")

        self.smooth_x, self.smooth_y = 0.5, 0.5

        # screen size
        self.x_dim, self.y_dim = (1920, 1080)

        self.get_coords_thread = threading.Thread(target=self.get_coords, name="Coords Thread", daemon=True)
        self.get_coords_thread.start()


    
    def get_coords(self):

        topic, msg = self.sub.recv_multipart()
        print("Player 2 Joined")

        while True:

            topic, msg = self.sub.recv_multipart()
            gaze_position = loads(msg, raw=False)

            if gaze_position["name"] == self.surface_name:

                gaze_on_screen = gaze_position["gaze_on_surfaces"]

                if len(gaze_on_screen) > 0:

                    raw_x, raw_y = gaze_on_screen[-1]["norm_pos"]

                    # smoothing out the gaze so the mouse has smoother movement
                    self.smooth_x += 0.35 * (raw_x - self.smooth_x)
                    self.smooth_y += 0.35 * (raw_y - self.smooth_y)
                    x = self.smooth_x
                    y = self.smooth_y

                    y = 1 - y  # inverting y so it shows up correctly on screen
                    x *= int(self.x_dim)
                    y *= int(self.y_dim)
                    
                    self.x_ref = x
                    self.y_ref = y