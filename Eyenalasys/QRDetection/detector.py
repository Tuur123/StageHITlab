import cv2

detector = cv2.QRCodeDetector()

vidcap = cv2.VideoCapture('Eyenalasys\QRDetection\\Hester.mp4')
success, img = vidcap.read()

video_fps = vidcap.get(cv2.CAP_PROP_FPS),
total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
height = vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
width = vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)

writer = cv2.VideoWriter("Eyenalasys\QRDetection\output.mp4", cv2.VideoWriter_fourcc(*'mp4v'), video_fps[0], (int(width), int(height)))

stap = ''

while success:   

    data, bbox, straight_qr_code = detector.detectAndDecode(img)
        
    # check if there is a QRCode in the image
    if bbox is not None:

        points = bbox[0]
        for i in range(len(points)):
            pt1 = [int(val) for val in points[i]]
            pt2 = [int(val) for val in points[(i + 1) % 4]]
            cv2.line(img, pt1, pt2, color=(255, 0, 0), thickness=3)

        if data:
            print("[+] QR Code detected, data:", data)

    # display the result
    cv2.imshow("img", cv2.resize(img, (900, 700)))    
    if cv2.waitKey(1) == ord("q"):
        break
    
    success, img = vidcap.read()

cv2.destroyAllWindows()
vidcap.release()
writer.release()