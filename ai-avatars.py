import os
import replicate
import urllib.request
import hashlib
from delphifmx import *

# Set the API token for Replicate
os.environ["REPLICATE_API_TOKEN"] = "replicate_com_api_key"

class FluxPulidApp(Form):

    def __init__(self, owner):
        # Setting up the style and form properties
        self.stylemanager = StyleManager(self)
        self.stylemanager.SetStyleFromFile("Air.style")

        self.SetProps(Caption="AI Avatars with Flux Pulid and Replicate API", OnShow=self.__form_show, OnClose=self.__form_close)

        # Layout for the top components (Button, Label, and Memo for prompt)
        self.layout_top = Layout(self)
        self.layout_top.SetProps(Parent=self, Align="Top", Height="50", Margins=Bounds(RectF(3, 3, 3, 3)))

        # Layout for the left components (Memo for prompt and file upload button)
        self.layout_left = Layout(self)
        self.layout_left.SetProps(Parent=self, Align="Left", Width="300", Margins=Bounds(RectF(3, 3, 3, 3)))

        # Label to prompt the user for image upload
        self.prompt_label = Label(self)
        self.prompt_label.SetProps(Parent=self.layout_top, Align="Client", Text="Enter the prompt and select the main face image:", Position=Position(PointF(20, 20)), Margins=Bounds(RectF(3, 3, 3, 3)))

        # Memo control for entering the prompt
        self.prompt_memo = Memo(self)
        self.prompt_memo.SetProps(Parent=self.layout_left, Align="Top", Height=60, Text="superhero flying above planet Earth", Margins=Bounds(RectF(3, 3, 3, 3)))

        # Button to trigger file upload
        self.upload_button = Button(self)
        self.upload_button.SetProps(Parent=self.layout_top, Align="Right", Text="Select Face Image", Position=Position(PointF(290, 18)), Width=120, OnClick=self.__upload_image, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Image control for the original image display
        self.img_original = ImageControl(self)
        self.img_original.SetProps(Parent=self.layout_left, Align="Client", Position=Position(PointF(20, 60)), Width=300, Height=300, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Image control for the generated output display
        self.img_output = ImageControl(self)
        self.img_output.SetProps(Parent=self, Align="Client", Position=Position(PointF(340, 60)), Width=300, Height=300, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Status bar at the bottom
        self.status_bar = Label(self)
        self.status_bar.SetProps(Parent=self, Align="Bottom", Text="Status: Ready", Height=30, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Timer for updating the status periodically
        self.timer = Timer(self)
        self.timer.Interval = 1000  # Timer event will trigger every second
        self.timer.Enabled = False
        self.timer.OnTimer = self.__on_timer_tick

        # Initialize variables for prediction handling
        self.prediction = None
        self.main_face_image_path = None

    def __form_show(self, sender):
        self.SetProps(Width=700, Height=450)

    def __form_close(self, sender, action):
        self.timer.Enabled = False
        action = "caFree"

    def __upload_image(self, sender):
        self.timer.Enabled = False

        open_dialog = OpenDialog(self)
        open_dialog.Filter = "Image Files|*.png;*.jpg;*.jpeg"
        open_dialog.Title = "Select Main Face Image"

        if open_dialog.Execute():
            file_path = open_dialog.FileName
            self.main_face_image_path = file_path
            self.img_original.LoadFromFile(file_path)
            self.status_bar.Text = "Status: Uploading and processing image..."
            self.upload_button.Enabled = False  # Disable upload button during processing
            Application.ProcessMessages()
            self.__start_processing(file_path, self.prompt_memo.Text)

    def __start_processing(self, file_path, prompt_text):
        try:
            # Use Replicate's async process for Flux Pulid
            model = replicate.models.get("zsxkib/flux-pulid")
            version = model.versions.get("8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b")
            self.prediction = replicate.predictions.create(
                version=version,
                input={
                    "width": 896,
                    "height": 1152,
                    "prompt": prompt_text,
                    "true_cfg": 1,
                    "id_weight": 1,
                    "num_steps": 20,
                    "start_step": 4,
                    "num_outputs": 1,
                    "output_format": "webp",
                    "guidance_scale": 4,
                    "output_quality": 80,
                    "main_face_image": open(file_path, "rb"),
                    "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs",
                    "max_sequence_length": 128
                }
            )
            self.timer.Enabled = True  # Enable the timer to start checking the status
        except Exception as e:
            self.status_bar.Text = f"Status: Error occurred - {str(e)}"
            self.upload_button.Enabled = True  # Re-enable the upload button

    def __on_timer_tick(self, sender):
        if self.prediction is None:
            return

        try:
            self.prediction.reload()
            if self.prediction.status == "processing":
                lines = self.prediction.logs.strip().split('\n')
                status = lines[-1] if lines else self.prediction.status
                self.status_bar.Text = f"Status: {status}..."

            elif self.prediction.status in ["succeeded", "failed", "canceled"]:
                self.timer.Enabled = False  # Disable the timer when the process finishes
                if self.prediction.status == "succeeded":
                    image_url = self.prediction.output[0]  # Get the first output image URL
                    file_name = './' + hashlib.md5(image_url.encode()).hexdigest() + '.webp'
                    urllib.request.urlretrieve(image_url, file_name)

                    # Display the output image
                    self.img_output.LoadFromFile(file_name)
                    self.status_bar.Text = "Status: Generation complete!"
                else:
                    self.status_bar.Text = f"Status: Generation failed with status: {self.prediction.status}"
                self.upload_button.Enabled = True  # Re-enable the upload button
        except Exception as e:
            self.status_bar.Text = f"Status: Error occurred - {str(e)}"
            self.timer.Enabled = False
            self.upload_button.Enabled = True  # Re-enable the upload button

def main():
    Application.Initialize()
    Application.Title = "AI Avatars with Flux Pulid and Replicate API"
    Application.MainForm = FluxPulidApp(Application)
    Application.MainForm.Show()
    Application.Run()
    Application.MainForm.Destroy()

if __name__ == '__main__':
    main()
