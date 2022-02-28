# recipe-app-api
This is a Django API for managing recipes. The aim while building this project was to practice Docker and Docker-compose concepts as well as the Test Driven Development flow applied to unit tests. This project contains tests for models, views, admin panel, django commands, image uploading and more.

## :bookmark_tabs: How to execute this project

1 - Execute the following command on the project's root folder
```
sudo docker-compose up
```

## :bookmark_tabs: How to run the tests
1 - Execute the following command on the project's root folder

```
sudo docker-compose run app sh -c "python manage.py test"
```

