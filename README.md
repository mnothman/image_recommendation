testing algorithm for user interactions <br/>
including interactions such as likes, comments, watch time per image and showing more content geared toward the user preference

<br/> folder: image rec final testsqlflask <br/> 


steps: <br/>
1. remove existing dataset and folder (if existing already) <br/>
rm -rf data/validation/data <br/>
(may need to elevate permissions to delete)<br/>
<br/>

2. python ./app.py

3.
build: <br/>
make build <br/>
<br/>

4.
run: <br/>
make run <br/>

5. Stop/Remove/Clean:
make stop

make remove

make clean

home page displays a wide range of content and the users interactions are recorded <br/>
these recorded interactions are weighted upon their strengths to show content geared toward the user on the image recommendations page <br/>

![updatedpict1](https://github.com/user-attachments/assets/2e3f6987-169f-4d62-8304-8b2e11966d66) <br/>
<br/>

![updatedpict2](https://github.com/user-attachments/assets/724e3bea-390f-4084-a0e8-28ddc656e003)
<br/>
<br/>

Using resnet50 for image classification  <br/>
Machine learning implementation: <br/>

1. Build and run project, and interact with images by liking and commenting <br/>

2. Train model <br/>
http://localhost:5000/train_model <br/>
This triggers training process inside docker container at "/app/data/recommender_model.pkl" <br/><br/>

3. View recommendations tab which should better reflect interactions consistent with images liked and commented <br/><br/>

4. Inspect / debug model: <br/>
Check trained model using check_model.py script <br/> <br/>

First option: <br/>
i. Enter container shell (docker must be running: make build / make run/ docker ps -a (for logs: docker logs image_recommendation_container)) <br/> <br/>
docker exec -it image_recommendation_container /bin/bash <br/> <br/>
 
ii. python check_model.py <br/> <br/>
![debugterminal](https://github.com/user-attachments/assets/12719cf1-d3d5-42ec-8459-156d4bbcfc9a)

<br/>
Second option: <br/>
Or go to route: http://localhost:5000/debug_model <br/><br/>

![debuggoogle](https://github.com/user-attachments/assets/43dfd5fc-b832-4a94-8867-ffd9e60a8c31)

<br/><br/>


In this example the user mainly interacted with labels such as cars and vehicles on the general page, therefore they are displayed images based upon these in their recommended tab: <br/>
![recommend1](https://github.com/user-attachments/assets/156cc80e-0db1-4a96-b2d7-5ae26d6d2840) <br/>

![recommend2](https://github.com/user-attachments/assets/399f8922-bfd9-4714-8594-0f13c1dcd78e) <br/>
<br/>
<br/>
<br/>