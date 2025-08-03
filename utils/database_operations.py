# This module requires a connected camera and the following libraries:
# pip install opencv-python pyzbar
import cv2
from pyzbar.pyzbar import decode

class BarcodeScanner:
    """
    Handles barcode and QR code scanning functionality using a live camera feed.
    """
    def start_scanner(self, on_scan_callback):
        """
        Opens a camera feed to scan for a barcode or QR code.
        
        Args:
            on_scan_callback: A function to call with the decoded data once a code is found.
                              The scanner window will close after a successful scan.
        """
        cap = cv2.VideoCapture(0) # 0 is the default camera
        if not cap.isOpened():
            print("Error: Could not open camera.")
            on_scan_callback(None)
            return

        print("Scanner started. Show a barcode/QR code to the camera. Press 'q' to quit.")
        
        scanned_code = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Decode any barcodes or QR codes in the frame
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                scanned_code = obj.data.decode('utf-8')
                print(f"Code found: {scanned_code}")
                # Draw a rectangle around the found code
                (x, y, w, h) = obj.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                break # Exit after finding the first code

            cv2.imshow("Barcode Scanner (Press 'q' to close)", frame)

            # If a code was found, stop the scanner and return the value
            if scanned_code:
                break
            
            # Allow user to quit manually
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Call the callback function with the result
        on_scan_callback(scanned_code)

# Example of how to use this class
def my_callback(code):
    if code:
        print(f"The scanner found the code: {code}")
    else:
        print("Scanner was closed without finding a code.")

if __name__ == '__main__':
    scanner = BarcodeScanner()
    scanner.start_scanner(my_callback)
