import cv2
import numpy as np
import os


class ImageProcessor:
    def __init__(self):
        self.exts = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")

    def is_visually_mono(self, img_path):
        """Loads image and checks if it is visually grayscale/mono."""
        img = cv2.imread(img_path)
        if img is None:
            return False

        # Check if 1-channel or if all 3 channels are identical
        if len(img.shape) < 3:
            return True

        b, g, r = cv2.split(img)
        return np.array_equal(b, g) and np.array_equal(g, r)

    def imgIdentifier(self, directory_path):
        """Returns two lists containing only filenames."""
        # 1. Get sorted list of all image filenames
        files = sorted(
            [f for f in os.listdir(directory_path) if f.lower().endswith(self.exts)]
        )

        # 2. Find the pivot point (first monochrome file)
        split_idx = len(files)
        for i, filename in enumerate(files):
            full_path = os.path.join(directory_path, filename)
            if self.is_visually_mono(full_path):
                split_idx = i
                break

        # 3. Create the sets of names
        color_set = files[:split_idx]
        mono_set = files[split_idx:]

        return mono_set, color_set


# --- MAIN USAGE ---
def main():
    proc = ImageProcessor()
    # Replace with your actual directory
    monos, colors = proc.imgIdentifier("./images")

    print("Mono Set:", monos)
    print("Color Set:", colors)


if __name__ == "__main__":
    main()
