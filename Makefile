install:
	pip install -r invictus/requirements/${ENV_REF}.txt

run:
	python manage.py runserver 0.0.0.0:9898 --settings=invictus.settings.${ENV_REF}

wsgi:
	gunicorn -w 3 invictus.wsgi:application -b :9898

migrate:
	python manage.py makemigrations --settings=invictus.settings.${ENV_REF}
	python manage.py migrate --settings=invictus.settings.${ENV_REF}

crawl_ogame:
	python manage.py crawl_ogame --settings=invictus.settings.${ENV_REF}

target: crawl_ogame run

pipe:
	make install
	make migrate
	make -j2 target

shell:
	python manage.py shell --settings=invictus.settings.${ENV_REF}