# My Urban Trails 

An app allowing you to plan out walking routes in urban areas.  Built with Mapbox, Flask and Postgresql.

## Table of Contents
* [Project overview](#project-overview)
* [Technologies Used](#technologies-used)
* [Features](#home)
* [Setup](#setup)
* [Files](#files)
* [Usage](#usage)
* [Project Staus](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)


## Project overview
Most map software allows for two endpoints and then calculates direction, distance and estimated time between those points.  Urban Trails allows you to plot out your own route by selecting continuous set of way point along the route.  A Mapbox API utility then returns an optimized route with distance and elapsed time.  For walking, it will connect visible streets and paths (parks and green spaces).  This feature is something I wanted for myself, and was inspired by the desktop app Microsoft Streets & Trips prior to widespread adoption of cellular mapping apps.

## Technologies Used

**Client:** Mapbox GL JS, Mapbox Matching API, Mapbox Draw, Bootstrap5

**Server:** Python, Flask, SQLalchemy

**Database**: Postgresql

## Features

- Selectively plot a map route for walks
- Determine distance and time estimates
- Supports Authenticated Users
- Stores user profiles
- Stores and recalls user trail routes


## Setup

The current version of this app works best on a large screen desktop.  You can clone the repository and set it up as a local host for personal development

You will need to create an account with Mapbox.com and obtain token.  Simply replace your token with the one in the map.js file.

You will also need to setup Python, Flask, SQLalchemy and Postgresql.  See the requirements.txt for the versions currently used, though installing latest supported version should work. Recommend using a venv environment for the development.

## Files
[Back to Top](#my-urban-trails)

| File      | Description                |
| :-------- | :------------------------- |
| `static/app.js` | Map display, Map API requests & Flask Requests |
| `static/styles.css` | Styles to position Map object |
| `templates/base.html` | Base template Flask Jinja |
| `templates/home.html` | Home page view, default route |
| `templates/login.html	` | Login page view |
| `templates/profile.html` | User profile page view |
| `templates/register.html` | Registration page view |
| `templates/userpage` | User page view |
| `app.py` | Runs Flask server |
| `forms.py` | Holds Flask WTForms |
| `models.py` | Flask SQLalchemy models |
| `seed.py` | builds Postgresql db with seed data |
| `tests.py` | unittests for the view routes |
| `downtheroad.py` | future routes to add a notes feature |
| `requirements.txt` | app requirements |


Once all of the above packages are installed You will need to setup a database in postgresql as follows:
from the ipython repl, run the seed.py file.  This will setup the databases and populate with some test data.

Once the database is live, run the flask server and go the the localhost:5000.  The default route will display the homepage.


## Usage
[Back to Top](#my-urban-trails)

The map part of the app utilizes the Mapbox GL JS library.  References to all of the required mapbox css and js libraries are included in the /templates/base.html page.

**Locating and styling the amp object in the document.** An object is placed on the web page inside a div.  The info box is place below and overlays the map:

```
<div id='map'></div>

<div class="info-box">
     <div id="info">
          <p>... instructions ...</p>
     </div>
     <div id="directions"></div>
</div>
```

Both these elements are set to absolute positions in the document, and positioned such that Bootstrap Navbar and the side column are place around.  See /static/styles.css.

The rest of the mapping elements are within the map.js file.

**Getting a mapbox access token.** An account will need to be created with Mapbox to obtain a token.  The token is added to the map object as shown and included at the beginning of the map.js file:

`mapboxgl.accessToken = '<mapbox token string>'`


**Setting up the Mapbox GL JS object.** Next, the mapbox map object is created.  As such:

```
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: defaultLocation,
    zoom: 14
});
```

**Adding map features.** Features can be added to the map objects.  In this example, a pointer indicating the center of the map and full-screen, navigation controls are added:

```
map.addControl(new mapboxgl.FullscreenControl());

const nav = new mapboxgl.NavigationControl();
map.addControl(nav, 'top-right');
```

[Back to Top](#my-urban-trails)

**Setting up the Mapbox Draw Object.** In order to draw in the map, to construct the route, the Mapbox drawing object is used.  It allows the user to draw various object over the map.  For this app, a polyline tool and delete route tool are added.  A new draw object is created with styles:

```
const draw = new MapboxDraw({
    // Instead of showing all the draw tools, show only the line string and delete tools
    displayControlsDefault: false,
    controls: {
      line_string: true,
      trash: true
    },
    styles: [
      // Set the line style for the user-input coordinates
      {
        "id": "gl-draw-line",
        "type": "line",
        "filter": ["all", ["==", "$type", "LineString"],
          ["!=", "mode", "static"]
        ],
        "layout": {
          "line-cap": "round",
          "line-join": "round"
        },
        "paint": {
          "line-color": "#438EE4",
          "line-dasharray": [0.2, 2],
          "line-width": 4,
          "line-opacity": 0.7
        }
      },
      // Style the vertex point halos
      {
        "id": "gl-draw-polygon-and-line-vertex-halo-active",
        "type": "circle",
        "filter": ["all", ["==", "meta", "vertex"],
          ["==", "$type", "Point"],
          ["!=", "mode", "static"]
        ],
        "paint": {
          "circle-radius": 12,
          "circle-color": "#FFF"
        }
      },
      // Style the vertex points
      {
        "id": "gl-draw-polygon-and-line-vertex-active",
        "type": "circle",
        "filter": ["all", ["==", "meta", "vertex"],
          ["==", "$type", "Point"],
          ["!=", "mode", "static"]
        ],
        "paint": {
          "circle-radius": 8,
          "circle-color": "#438EE4",
        }
      },
    ]
});
```

**Adding Drawing tools to the map object.** The drawing tool is then added to the map object as follows.  This allow then allow the user to scribe a polyline representing a desired route on the map by selecting a set of points as along the route:

```
map.addControl(draw);

map.on('draw.create', updateRoute);
map.on('draw.update', updateRoute);  
map.on('draw.delete', removeRoute); 
```

[Back to Top](#my-urban-trails)

**Creating a route using a polyline.** Once a line is selected, the user clicks again on the last point and this event send the user plotted coordinates to the Mapbox Matching API.  Return is an optimized route with estimated time, distance and directions.  This information is then drawn on the map as an overlay.  The user can see the designed trail and the updated trail.  The user can then click the trash icon, delete the route and make a new route.  In this app, a logged in user can store the route.

**Accessing the Mapbox Matching API.**  The updateRoute() function extracts the coordinates form the user selected route, and sets up a profile that is used to access the Mapbox Matching api.  The access for this api is wrapped in the getMatch(coords, radius, profile) function.  The matching api returns the optimized route, which is then drawn on the map object.

*Note: Data returned from the Mapbox Matching API are placed in local storage (coordinates, distance and time).  Prior to each event, local storage is cleared such that only the current optimized map is retained.  This make the key data available if a user decides to name and save a route.*

See below:

```
let testData = {};
// Obtain a match from the Map Matching API
function updateRoute() {
    // Set the profile (driving, walking, cycling, driving-traffic)
    const profile = "walking";
    // Retrieve coordinates drawn on map
    const routeData = draw.getAll();
    testData = routeData;
    console.log('routeDate: ', routeData);
    const lastFeature = routeData.features.length - 1;
    const rawCoords = routeData.features[lastFeature].geometry.coordinates;
    // Format the coordinates for the API cal
    let coords = rawCoords.join(';');
    console.log(`coords: ${coords}`);
    
    // Set the radius for each coordinate pair (0 - 50) meters
    // Default is 5. set from 1-10 clean traces, and 20-50 noisy traces
    // A value us set for each coordinate pair
    const radius = [];
    const setRadius = 25;
    for(let i = 0; i < rawCoords.length; i++) {
        radius.push(setRadius)
    }
    
    // Invoke getMatch function retrieve API coordinates for map
    getMatch(coords, radius, profile);
}

// Generate a request to the Map Matching API
// Returns an optimized set of coordinates or an error function

getMatch(coordinates, radius, profile) {
    // Separate radiuses with semicolon
    const radiuses = radius.join(';');
    localStorage.clear();
    // Create query string for Map Matching API
    const query = 'https://api.mapbox.com/matching/v5/mapbox/' +
                    profile + '/' + 
                    coordinates + 
                    '?geometries=geojson&radiuses=' + 
                    radiuses + '&steps=true&access_token=' + 
                    mapboxgl.accessToken;

    $.ajax({
        method: 'GET',
        url: query
    }).done(function(data) {
        // Get the coordinates from the response
        const coords = data.matchings[0].geometry;
        console.log('Coordinates from Match: ', coords);
        console.log('JSON Data response: ', data);
        // Save to local storage
        localStorage.setItem('coords', JSON.stringify(coords));
        // Draw the route on the map
        addRoute(coords);
        // Add data and instructions to the directions box
        getInstructions(data.matchings[0]);
    });                    
}
```

[Back to Top](#my-urban-trails)

**Drawing the optimized route on the map.** The function addRoute(coords) is called after the Mapbox Matching API optimized route.  This function places the new route on the map.  Styling can be modified in via the addLayer JSON.

```
function addRoute(coords) {
    // Check for existing routes and remove them
    // Then, add new route layer
    if (map.getSource('route')) {
        map.removeLayer('route');
        map.removeSource('route');
    }
    else {
        // Add new layer to the map
        map.addLayer({
            "id": "route",
            "type": "line",
            "source": {
              "type": "geojson",
              "data": {
                "type": "Feature",
                "properties": {},
                "geometry": coords
              }
            },
            "layout": {
              "line-join": "round",
              "line-cap": "round"
            },
            "paint": {
              "line-color": "#03AA46",
              "line-width": 8,
              "line-opacity": 0.8
            }
        });
    }
}
```

[Back to Top](#my-urban-trails)

**Removing a user route.** The function is a callback function removeRoute() removes the drawn layer, triggered by clicking on the trash button event `map.on('draw.delete, removeRoute)`.

**Getting Map Directions.** Map directions are part of the response object returned by the Mapbox Matching API. The direction data is extraction from the response object and passed to the function as shown `getInstructions(data.matchings[0])`.  This function builds the html to display instructions and data in the info box that overlays the map. 

**Storing and Retrieving routes:** For logged in users, routes can be stored in the postgresql database via flask routes.  Event handler using jquery manage the storage and retrieval.  Axios GET and POST requests target flask routes respectively.  Information required for the route (userid and trailid) are included in the html template rendered by flask.

When a route is retrieved, the function `drawStoredMap(resp)` Draws the stored optimized route on the map object.

## Project Status

The project is: _in progress_

## Room for Improvement

- Improve the adding and deleting a stored map.  The store map draws correctly, yet doesn't delete the layer properly.

- Update the sections of the app w/o refreshing the map

- Center map based on current device location, or entered address

- Printable directions

- Add user notes to a stored map

- A mobile friendly version

## Acknowledgements
[Back to Top](#my-urban-trails)

- This project was inspired by the AllTrails app, except something that could be used in urban areas and have a design-your-own feature which is inspired by Streets & Trips

- The polyline drawing feature was inspired by this mapbox example app (https://docs.mapbox.com/help/tutorials/get-started-map-matching-api/) 
