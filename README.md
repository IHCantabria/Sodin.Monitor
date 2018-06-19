# SODIN Web

SODIN is an operational system for flooding damages, able to collect damage information originated during and after flooding episodes on rivers and coast.
SODIN Web is a web viewer that let the user locate and filter past events on a map and navigate through event's captured data on a user friendly timeline.

## Installation

1.  Restore data from _db_ folder (SodinBD and TestSodinBD) on your MongoDB server. For example:

```
mongorestore --archive= db/SodinBD/sodin.archive --host xxx.xxx.xxx.xxx:xxxx --nsFrom SodinBD.* --nsTo SodinBD.* --username xx --password xxx
```

2.  Rename _config.example.json_ to _config.json_, and set connection properties

```
{  
  "MongoDb": {
    "connection": "yourConnectionString",
    "name": "SodinBD"
  }
}
```

3.  Install grunt: `npm install -g grunt-cli`
4.  Run grunt task **build**
5.  Publish the web on IIS in your server

## Usage

Use your regular browser and navigate to the web site

## Contributing

1.  Fork it!
2.  Create your feature branch: `git checkout -b my-new-feature`
3.  Commit your changes: `git commit -am 'Add some feature'`
4.  Push to the branch: `git push origin my-new-feature`
5.  Submit a pull request :D

## Built With

- [Angular](https://angularjs.org/) - The web framework used
- [Grunt](https://gruntjs.com) - Task manager
- [Jasmine](https://jasmine.github.io/) - Testing framework

## Credits

[IH Cantabria](https://github.com/IHCantabria)

## License

Licensed under the GNU General Public License v3.0 - see the LICENSE.md file for details

At runtime it uses:

- [Timelinejs3](https://github.com/fmaturel/angular-timelinejs3) - MIT License
- [Leaflet](https://github.com/Leaflet/Leaflet) - [README.MD](https://github.com/Leaflet/Leaflet/blob/master/README.md)
- [Chart.js](https://github.com/chartjs/Chart.js) - MIT License
