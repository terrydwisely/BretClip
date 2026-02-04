"""Test the capture overlay directly."""

import sys
sys.path.insert(0, '.')

from PyQt5.QtWidgets import QApplication
from capture.modes import CaptureMode
from capture.selector import SelectionOverlay

app = QApplication(sys.argv)

print('Creating selection overlay...')
print('Click and drag to select an area, or press ESC to cancel')

selector = SelectionOverlay(CaptureMode.RECTANGULAR)

def on_complete(img):
    if img:
        print(f'Capture complete! Image size: {img.size}')
        img.save('test_capture.png')
        print('Saved to test_capture.png')
    else:
        print('Capture returned None')
    app.quit()

def on_cancel():
    print('Capture cancelled')
    app.quit()

selector.selection_complete.connect(on_complete)
selector.selection_cancelled.connect(on_cancel)

print('Showing overlay now...')
selector.show()

sys.exit(app.exec_())
