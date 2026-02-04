"""Clipboard operations for copying images."""

from PIL import Image
import io
import win32clipboard
import win32con


class ClipboardManager:
    """Manages clipboard operations for images."""

    @staticmethod
    def copy_image(image: Image.Image) -> bool:
        """Copy a PIL Image to the Windows clipboard.

        Args:
            image: PIL Image to copy

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to BMP format for clipboard
            output = io.BytesIO()

            # Ensure RGB mode (clipboard doesn't support RGBA well)
            if image.mode == 'RGBA':
                # Create white background and paste image
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            image.save(output, 'BMP')
            data = output.getvalue()[14:]  # Skip BMP header

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            win32clipboard.CloseClipboard()

            return True
        except Exception as e:
            print(f"Clipboard error: {e}")
            return False

    @staticmethod
    def get_image() -> Image.Image | None:
        """Get an image from the clipboard.

        Returns:
            PIL Image if available, None otherwise
        """
        try:
            win32clipboard.OpenClipboard()

            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                win32clipboard.CloseClipboard()

                # Add BMP header
                bmp_header = b'BM' + (len(data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                bmp_data = bmp_header + data

                return Image.open(io.BytesIO(bmp_data))
            else:
                win32clipboard.CloseClipboard()
                return None
        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            return None

    @staticmethod
    def clear():
        """Clear the clipboard."""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        except Exception:
            pass
