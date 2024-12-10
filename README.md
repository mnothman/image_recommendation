testing algorithm for user interactions <br/>
including interactions such as likes, comments, watch time per image and showing more content geared toward the user preference

<br/> folder: image rec final testsqlflask <br/> 


steps: <br/>
1. remove existing dataset and folder (if existing already) <br/>
rm -rf data/validation/data <br/>
(may need to elevate permissions to delete)<br/>
<br/>

2.
build: <br/>
make build <br/>
<br/>

3.
run: <br/>
make run <br/>

4. Stop/Remove/Clean:
make stop

make remove

make clean

home page displays a wide range of content and the users interactions are recorded <br/>
these recorded interactions are weighted upon their strengths to show content geared toward the user on the image recommendations page <br/>

In this example the user mainly interacted with labels such as cars and vehicles on the general page, therefore they are displayed images based upon these in their recommended tab: <br/>
![recommend1](https://github.com/user-attachments/assets/156cc80e-0db1-4a96-b2d7-5ae26d6d2840) <br/>

![recommend2](https://github.com/user-attachments/assets/399f8922-bfd9-4714-8594-0f13c1dcd78e) <br/>
