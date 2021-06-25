# Django REST Framework Image API  
  
REST API built using Django REST Framework providing ability to upload files and get links to original image and its thumbnails, according to Plan chosen by User.  
Additionally, provides ability to generate expiring links to images specified above (depends on plan settings).  
  
## Setup  
  
Clone repository, edit superuser credentials in `variables.env`, run `docker-compose up` from root directory and go to [localhost:8000](localhost:8000).

docker-compose sets up Python environment, Postgres database and memcached server.

## Requirements

- asgiref: 3.3.4
- Django: 3.2.4
- django-annoying: 0.10.6
- django-pymemcache: 1.0.0  
- django-rest-framework: 0.1.0  
- djangorestframework: 3.12.4  
- generics: 3.3.1  
- install: 1.3.4  
- Pillow: 8.2.0  
- pymemcache: 3.4.4  
- pytz: 2021.1  
- psycopg2: 2.9.1
- six: 1.16.0  
- sorl-thumbnail: 12.7.0  
- sqlparse: 0.4.1  
- uuid: 1.30

## Paths

|PATH|METHOD|BEHAVIOUR|
|---|:---:|:----:|
| /|GET  |API Root - links to list of user and list of images|
|/users/|GET|List of users with chosen plan|
|/images/|GET|Lists images of logged in user <br />`[  {  "url": ,  "uuid":  ,  "owner":  ,  "thumbnail": }  ]`|
|/images/|POST|Add new image|
|/images/<image_uuid>{?size=}|GET|Image or thumbnail (if size is specified) details <br />`{  "url":  ,  "uuid":  ,  "links":  {  "thumbnail_200px": optional ,  "thumbnail_400px": optional ,  "original": optional }  }`|
|/images/<image_uuid>{?size=}|DELETE|Delete image and its thumbnails|
|/images/<image_uuid>/link{?size=}|GET|Links: direct link to image or thumbnail and expiring link if generated <br />`{  "url":  ,  "uuid":  ,  "image_link":  ,  "expiring_link": optional ",  "temp_link_generator":  optional  }`|
|/images/<image_uuid>/get-temporary{?size=}|POST|Generate temporary link with given `duration`|
|/temp{?token=}|GET|Temporary link to image|
