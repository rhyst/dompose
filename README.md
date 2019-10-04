# Dompose

If you have lots of docker containers that you need to run, and they have complicated configurations or dependencies then you would likely start using Docker Compose. Docker Compose allows you to write config files for your containers, including setting up interdependent networks and volumes. It even allows you to specify whether containers depend on other containers and will then change the boot order to ensure that the dependencies start first.

But what if one of the dependencies needs to change because of a container that relies on it? For example, you have a PHP container, and you have website containers. The website container volumes need to be mounted in the PHP container, but the websites are dependent on the PHP container. Sure you could manually manage the compose file so that each time you add a new service you edit the config of the dependency but if you are frequently switching services in and out this is a pain. It would be better if the dependency container did not have to know anything about its dependants.

I wrote a Python script to add an extra layer of management around Docker Compose, called Docker Composer. It's inspired by the style of the uswgi manager `uswgi-emperor`.


# Installation

```
pip install dompose
```


## Usage

Start with a directory for your related services and include a 'services-available' folder, and a `.env` file.

```plaintext
my-services/
├── .env
└── services-available/
```

You can then add your interelated docker-compose services in the `services-available` folder.

```plaintext
my-services/
├── .env
└── services-available/
    ├── php.yml
    └── my-website.yml
```

The config files can just be docker-compose config files but you can also make user of extra composer features.

**php.yml**

```yaml
version: "3"
services:
  ${PHP_FPM_NAME}:
    build: /path/to/docker/file
    container_name: ${PHP_FPM_NAME}
    image: ${PHP_FPM_NAME}
    volumes:
    networks:
      - ${MY_NETWORK}
    restart: always
networks:
  ${MY_NETWORK}:
    driver: bridge
volumes:

composer_base: true
```

**my-website.yml**

```yaml
version: "3"
services:
  ${WEBSITE_NAME}:
    container_name: ${WEBSITE_NAME}
    image: nginx
    volumes:
      - /path/to/my/website:/var/www/website.com
    networks:
      - ${MY_NETWORK}
    depends_on:
      - ${PHP_FPM_NAME}
    restart: always
composer_compositions:
  - type: add
    value: /path/to/my/website:/var/www/website.com
    to:
      - services
      - ${PHP_FPM_NAME}
      - volumes
```

**.env**

```bash
PHP_FPM_NAME=php-fpm
WEBSITE_NAME=website
MY_NETWORK=web-network
```

The extra syntax visible in this example is:

- **Environment variables everywhere** e.g. `${WEBSITE_NAME}`  
  This is an improvement on the normal docker compose environment variable. You can even use them as service names. These are picked up from the .env file.
- **composer_compositions**  
  The syntax for modifying other services. In the example we want to `add` our file path mapping `/path/to/my/website:/var/www/website.com` to the php services volumes section. The `to` value is just the path within the yml file.
- **composer_base**  
  Composer will combine all the services into a single docker-compose.yml. To do this one config must be nominated as the `base` config. This could either be one that is expected to run all the time (as in the php example) or a blank config.

So with the configuration files in place you would enable them

```bash
dompose enable php
dompose enable my-website
```

Which would symlink them into a new folder `services-available`

```plaintext
my-services/
├── .env
├── services-available/
│   ├── php.yml
│   └── my-website.yml
└── services-enabled/
    ├── php.yml
    └── my-website.yml
```

Running the script once more

```bash
doompose
```

Will generate a `docker-compose.yml`

```plaintext
my-services/
├── .env
├── services-available/
│   ├── php.yml
│   └── my-website.yml
├── services-enabled/
│   ├── php.yml
│   └── my-website.yml
└── docker-compose.yml
```

And then you can use `docker-compose` as normal

```bash
docker-compose up -d
```

Enabling and disabling services is as simple as removing their files from the `services-enabled` folder, manually or using the inbuilt command

```bash
dompose disable my-website
```

You can also list a few more configuration arguments for dompose

```bash
./dompose --help
```

## Internals

There's nothing complicated in the script, so reading it probably isn't a terrible way to find out how it works.

The `enable`/`disable` commands work by adding and removing symlinks into the enabled folder, with some file system checking etc.

The main `run` command reads all the files from the enabled folder as strings. It firstly does a find/replace for all the environment variables and then it parses them into python dictionaries.

The base config is found and then that is used to recursively merge the dictionaries on top of that base. It does nothing clever to manage key collisions, the later read configs will simply overwrite earlier configs.

With the fully merged dictionary it runs through all of the compositions from each config and applies the changes specified.

Finally it dumps the dictionary to a yaml file.

## Limitations

- At the moment the only `composition` is the `add` composition which is the only one I have found useful. I can imagine uses for more verbs and it would not be too difficult to add them.
- It's not super clever. I think it could manage more of the bringing containers up and down itself, and do it automatically i.e wrap more of the docker-compose functionality so things can be done in fewer commands. A recompile and refresh/rebuild command might be nice. Though in some ways its nice to leave it simple and not try to solve solved problems.

