This is a very simple program to automatically edit your videos by removing silences from them.

### Before using the editor
Make sure to install the dependencies:
- **moviepy**: Used for video editing operations such as cutting and concatenating video clips.
- **pydub**: Used for audio processing tasks like silence detection and audio editing.

```bash
pip install moviepy pydub
```


### Using the editor
In order to use the program, you'll need to call the python code with certain command line arguments, like so:
```bash
python auto_editor.py <input_path> <output_path> --optional_args
```

The arguments accepted are as follows:
   * input_path: Mandatory. The path of your video.
   * output_path: Mandatory. The path where the edited video will be written.
   * --silence_threshold: Optional. The minimum time in ms to cut for a silence.
   * --padding_left: Optional. The amount of time in ms that will be kept before a silence cut.
   * --padding_right: Optional. The amount of time in ms that will be kept after a silence cut.
   * --silence_db_threshold: Optional. The volume threshold in dB to take as a "silence". 
   * --verbose: Optional. If True, will show more information regarding the operation of the program.
   * --debug: Optional. If True, will show a lot of information regarding the operation of the program.


### After using the editor
No attribution needed when using, modifying, extending, forking, etc this piece of code. Check out the MIT licence: https://opensource.org/license/mit.
