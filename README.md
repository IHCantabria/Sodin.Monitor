# SODIN Monitor

SODIN is an operational system for flooding damages, able to collect damage information originated during and after flooding episodes on rivers and coast.
SODIN Monitor is a operational process with three main goals: Detection, Management, and Analysis of events. After all processes have finished, results are
saved on a database ready to be consumed by applications.

## Installation

1.  Restore data from _db_ folder (SodinBD and TestSodinBD) on your MongoDB server. For example:

```
mongorestore --archive= db/SodinBD/sodin.archive --host xxx.xxx.xxx.xxx:xxxx --nsFrom SodinBD.* --nsTo SodinBD.* --username xx --password xxx
```

2.  Rename _config.example.py_ to _config.py_, set connection properties and api keys values

```
# API Keys Microsoft Cognitive Services (AZURE) #
COMPUTER_VISION_API_KEY = ''
FACE_API_KEY = ''
TEXT_API_KEY = ''

# BD Connection #
URI_MONGODB = ''
# Temp Folder #
RUTA_BASE_EJECUCIONES = ''
```

3.  Do the same for all config files ending with _example_

## Usage

Run **monitor_sodin.py** or/and **gestor_sodin.py**

## Contributing

1.  Fork it!
2.  Create your feature branch: `git checkout -b my-new-feature`
3.  Commit your changes: `git commit -am 'Add some feature'`
4.  Push to the branch: `git push origin my-new-feature`
5.  Submit a pull request :D

## Built With

- [Python](https://www.python.org/) - The operational system environment
- [MongoDB](https://www.mongodb.com/) - The Database
-

## Credits

[IH Cantabria](https://github.com/IHCantabria)

## License

Licensed under the GNU General Public License v3.0 - see the LICENSE.md file for details

At runtime it uses:

- [Cognitive Services](https://azure.microsoft.com/es-es/services/cognitive-services/)
- [PyMongo](https://api.mongodb.com/python/current/)
- [Twython](https://twython.readthedocs.io/en/latest/)
