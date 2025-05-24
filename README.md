# recipea

* Get your Gemini API key here: https://aistudio.google.com
* Add it to .env file in the recipea folder
* Install Docker on your machine
* Then run `docker-compose up --build`
* Website is accessible on http://localhost:5001/
It might take a bit more time on the first run while it installs all dependencies and downloads the model

If you have a large RAM, you can increase the RAM dedicated to docker to 16GB and set WHISPER_MODEL_NAME=large-v3 to increase the accuracy of the transcription
