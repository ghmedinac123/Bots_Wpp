import sys
import base64
import io
from PIL import Image, ExifTags

def save_base64_image(base64_str, file_path):
    # Decode the base64 string
    image_data = base64.b64decode(base64_str)
    with open(file_path, "wb") as f:
        f.write(image_data)
    print(f"Image saved to {file_path}")

def extract_coordinates(file_path):
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()

        if not exif_data:
            raise ValueError("No EXIF metadata found")

        exif = { ExifTags.TAGS[k]: v for k, v in exif_data.items() if k in ExifTags.TAGS }
        gps_info = exif.get('GPSInfo')

        if not gps_info:
            raise ValueError("No GPS metadata found")

        def get_decimal_from_dms(dms, ref):
            degrees = dms[0]
            minutes = dms[1]
            seconds = dms[2]
            decimal = degrees + minutes / 60.0 + seconds / 3600.0
            if ref in ['S', 'W']:
                decimal = -decimal
            return decimal

        lat = get_decimal_from_dms(gps_info[2], gps_info[1])
        lon = get_decimal_from_dms(gps_info[4], gps_info[3])

        return {"latitude": lat, "longitude": lon}

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_coordinates.py <base64_string> <output_image_path>")
        sys.exit(1)

    base64_str = sys.argv[1].replace(' ', '+').replace('\n', '').replace('\r', '').strip()
    output_image_path = sys.argv[2]

    save_base64_image(base64_str, output_image_path)
    coordinates = extract_coordinates(output_image_path)
    print(coordinates)
