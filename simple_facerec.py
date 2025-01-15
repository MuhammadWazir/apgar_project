import face_recognition
import cv2
import requests
import numpy as np

class SimpleFacerec:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []

        # Resize frame for a faster speed
        self.frame_resizing = 0.25

    def load_encoding_from_api(self, api_url):
        """
        Load face encodings and names from a FastAPI endpoint
        :param api_url: URL of the FastAPI endpoint
        """
        response = requests.get(api_url)
        if response.status_code == 200:
            face_data = response.json()
            
            # Extract names and encodings
            for item in face_data:
                self.known_face_ids.append(item["id"])
                self.known_face_encodings.append(np.array(item["face_encoding"]))
            print("Encodings loaded from API")
        else:
            print(f"Failed to fetch data from API: {response.status_code}")

    def detect_known_faces(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        # Convert the image from BGR color (OpenCV) to RGB color (face_recognition)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_id_dictionary = {}

        for face_encoding in face_encodings:
            # Compare the current face encoding with known encodings
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                id = self.known_face_ids[best_match_index]
                distance = face_distances[best_match_index]
                face_id_dictionary[id] = distance

        # Return the ID with the smallest distance or "-99" if the dictionary is empty
        if face_id_dictionary:
            return min(face_id_dictionary, key=face_id_dictionary.get) 
        else:
            return -99
