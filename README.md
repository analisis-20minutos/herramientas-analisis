# Herramientas de scrapeado y análisis para __20minutos__

Este repositorio contiene todos los proyectos y scripts desarrollados durante el trabajo de investigación descrito en el artículo __"Creación de un corpus de noticias de gran tamano en espanol para el análisis diacrónico y diatópico del uso del lenguaje"__. Con estos, se puede replicar localmente el corpus descrito en este trabajo para su posterior análisis.

## Requisitos/Sistemas Utilizados
* [Ubuntu 18.04](http://releases.ubuntu.com/18.04/) (también [Linux Mint 18.3](https://linuxmint.com/edition.php?id=246))
* [Python 3.7](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (con el 3.6 también debería funcionar bien)
* [Scrapy](https://doc.scrapy.org/en/latest/intro/install.html)
* [GCC8](https://askubuntu.com/questions/1028601/install-gcc-8-only-on-ubuntu-18-04)
* [Freeling 4.1](https://talp-upc.gitbook.io/freeling-4-1-user-manual/installation/installation-packages)

## Instrucciones de uso
Este repositorio consta de dos proyectos, el de scrapeado web y el de analizador de textos, además de algunos pequeños scripts como el eliminador de duplicados, el de generador de CSVs para análisis o el limpiador de stopwords para los CSVs.
### Scrapeado web
Primero es necesario realizar todo el volcado de noticias del archivo de 20minutos. Para ello, debemos de ejecutar el spider desde el proyecto de Scrapy (crawler):

```bash
scrapy crawl 20minutos -o dump.jl -s JOBDIR=crawls/20minutos-1
```

Esto generará una estructura de directorios en `~/dump/` con el formato `provincia/año/mes/día/`, en cada uno de los cuales tendremos las noticias de un día para una provincia.

Podemos ajustar el rango de fechas que queremos obtener desde el fichero `crawler/scrapy.cfg` y las provincias desde `crawler/admitted_cateogories.txt`.

### Eliminador de duplicados
Es un pequeño script que busca noticias duplicadas en el corpus (que deberá estar en `~/dump/`) y las elimina, dejando solamente un único ejemplar (el primero). Se han utilizado estructuras basadas en MinHash y LSH prestando especial atención al rendimiento y la eficiencia. Para ejecutarlo, implemente llamamos al script y funciona:

```bash
python duplicates_remover.py
```

Podemos ajustar el rango de fechas a buscar en `config.cfg`, las provincias desde `admitted_cateogories.txt` y la sensibilidad de la similitud entre dos noticias en la variable `THRESHOLD` del propio script.

### Analizador de textos para las noticias
Este proyecto utiliza la librería Freeling para realizar un análisis textual con técnicas NLP gracias al cual podemos agregar información de utilidad a las noticias originales (en `~/dump/`). Aun estando paralelizado con OpenMP, es un proceso muy lento. Por tanto, se recomienda antes haber eliminado las noticias duplicadas.

Existe un script que compila y ejecuta el proyecto, así que simplemente lo ejecutamos para ponerlo en marcha:

```bash
./compile_and_run.sh
```

Podemos detener y reanudar el programa siempre que queramos, pues hay un registro de ficheros procesados en `processed_files.txt`. Si queremos comenzar de nuevo, deberemos de borrar `~/dump/`, obtener las noticias de nuevo, borrar el fichero de noticias procesadas y ejecutar el binario compilado.

### Procedimientos para generar CSVs de estadísticas de las noticias
En `news_stats.py` tenemos una serie de simples funciones que recogen cierta información de las noticias para generar CSVs con estadísticas concretas sobre un concepto. Estas funciones podrán parecer repetitivas y podrían haberse desarrollado de mejor forma, pero no era esa la intención, pues la mayoría de estas fueron escritas desde el REPL de Python y posteriormente copiadas al fichero para dejar ejemplos de cómo se han recogido algunos de los datos.

Para ejecutar un procedimiento, debemos de modificar el main para hacer una llamada u otra con los parámetros que necesitemos y ejecutarlo:

```bash
vi news_stats.py
python news_stats.py
```

Al igual que en otros scripts, podemos ajustar el rango de fechas a buscar en `config.cfg` y las provincias desde `admitted_cateogories.txt`.

Algunos de los CSVs generados son de tal tamaño que resulta impracticable abrirlos en un programa de hojas de cálculo convencional. Una posible solución puede ser la de montar una base de datos [MariaDB](https://mariadb.com/) en donde tengamos una tabla equivalente al CSV para poder [importarlo](http://www.mysqltutorial.org/import-csv-file-mysql-table/). Se recomienda usar para la tabla un motor sin claves ajenas como [MyISAM](https://mariadb.com/kb/en/library/myisam-storage-engine/) o [TokuDB](https://mariadb.com/kb/en/library/tokudb/) (también disponible en [docker](https://hub.docker.com/r/goldy/tokudb/)). También se recomienda generar índices para cada una de las columnas una vez se hayan insertado todas las filas.

### Limpiador de stopwords para los CSVs generados
Para eliminar las stopwords (si procede) de un CSV generado con los anteriores procedimientos, podemos ejecutar este script que eliminará aquellas entradas cuya palabra esté en `stopwords-es.txt`.

```bash
python stopwords_remover.py -i in.csv -o out.csv
```

También podemos configurar el delimitador de columnas con `-d` o `--delimiter` y el nombre de la columna en donde debe buscar el nombre con `-c` o `--col_name`.

### ¡Extra!
También se incluye otra serie de archivos extra: 
* Un excel con los datos extraídos para los experimentos realizados posteriormente.
* Las propias infografías como resultado de estas.
* Una lista de anglicismos en `anglicisms.txt`
* El borrador del artículo en PDF.
