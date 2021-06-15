
// Token object
mapboxgl.accessToken = 'pk.eyJ1IjoiZ2FkYW1zODg1IiwiYSI6ImNrcHZndzJrNjFhZmsycXFycnl2ejkxZmwifQ.TlHaR8imAHiVAfYR-sZ62A';

// Map starting point in longitude, latitude (hardcode)
const defaultLocation = [-121.608704, 36.703205];
const URL = 'http://127.0.0.1:5000'


/********************************************************/
/*  FIND CURRENT LOCATION TO CENTER MAP                 */
/********************************************************/
// Setup map based on current location
// Uses device based location services Navigator.geolocation
let centerPoint = {};

// Navigator.geolocation callback functions (success, error, options)
function positionSuccess(pos) {
    console.log(pos);
    // Extracts current location
    // centerPoint = {
    //     'lng': pos.coords.longitude,
    //     'lat': pos.coords.latitude
    // };

    centerPoint['lng'] = pos.coords.longitude;
    centerPoint['lat'] = pos.coords.latitude;

    console.log('centerPoint: ', centerPoint);
    
}

function positionError() {
    console.log('Location Services not Available, using default');
    
    centerPoint = {
        'lng': defaultLocation[0],
        'lat': defaultLocation[1]
    };
    
    console.log(centerPoint);
}


// Set options
const positionOptions = {
    enableHighAccuracy: true,
    timeout: 500,
    maximumAge: 0
}

// Get current location from DOM

// Test if location available in browser
if (!navigator.geolocation) {
    console.log('Geolocation not supported');
}
else {
    console.log('locating... sort of');
    navigator.geolocation.getCurrentPosition(positionSuccess,
            positionError,
            positionOptions);
}
   
/********************************************************/
/*  ESTABLISH BASE MAPBOX GL JS OBJECT                  */
/********************************************************/

// Define Main map object
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: defaultLocation,
    zoom: 14
});
  
// Add postion marker as center for displayed map
const marker = new mapboxgl.Marker(
    {
        anchor: 'center',
        draggable: true
    }
    ).setLngLat(defaultLocation)
    .addTo(map);
// Adds Fullscreen control
map.addControl(new mapboxgl.FullscreenControl());
// Adds directions controls
// map.addControl(directions, 'top-left');
// Adds zoom controls
const nav = new mapboxgl.NavigationControl();
map.addControl(nav, 'top-right');
  

/********************************************************/
/*  ESTABLISH MAPBOX GL DRAWING OBJECT TO DESING ROUTES */
/********************************************************/

// Create a new Draw plugin object
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

// Add the drawing tool object to the map
map.addControl(draw);
// Set up route from draw objects
map.on('draw.create', updateRoute);
map.on('draw.update', updateRoute);  
map.on('draw.delete', removeRoute); 

/********************************************************/
/*  RETRIEVE OPTIMIZED ROUTE FROM MAPBOX API            */
/*  PREPARE Coordinates, Distance, Duration             */
/*  and direction.  DRAW NEW ROUTE ON MAP               */
/********************************************************/

// Retrieve coordinates drawn on the map via the draw tools
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
    
    // Set the radious for each coordinate pair (0 - 50) meters
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
// Returns an optimized set of coordinates or an error
function getMatch(coordinates, radius, profile) {
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
        console.log('JSON Data reponse: ', data);
        // Save to local storage
        localStorage.setItem('coords', JSON.stringify(coords));
        // Draw the route on the map
        addRoute(coords);
        // Add data and instructions to the directions box
        getInstructions(data.matchings[0]);
    });                    
}

// Draw the Map Matching route as a new map layer
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

// Remove route when user clicks delete draw button
// removes the layer if exists
function removeRoute() {
    if (map.getSource('route')) {
        map.removeLayer('route');
        map.removeSource('route');
    }
    else {
        return;
    }
}

function getInstructions(data) {
    // Target the sidebar to add the instructions
    const directions = document.getElementById('directions');

    const legs = data.legs;
    let tripDirections = '';
    // Obtain instructions for each leg of the route
    for (let i = 0; i < legs.length; i++) {
        let steps = legs[i].steps;
        for (let j = 0; j < steps.length; j++) {
            tripDirections = tripDirections + `<h5>- ${steps[j].maneuver.instruction}</h5>`;
        }
    }
    console.log('Trip Direction', tripDirections);
    // Convert stats from metric to english
    // Add function to manage different units metric/english
    const tripDuration = (data.duration / 60).toFixed(1);
    const tripLength = (data.distance / 1609.344).toFixed(2);
    localStorage.setItem('duration', JSON.stringify(tripDuration));
    localStorage.setItem('distance', JSON.stringify(tripLength));
    directions.innerHTML = '<h4>Trip duration: ' +
                            tripDuration + ' mins<h4>'+
                            '<h4>Trip length: ' +
                            tripLength + ' miles<h4>'+ 
                            '<h4>Directions: </h4>' +
                            tripDirections;

}

// Add code and methods to store the route
// Collect user data from form
// Prep route data for storage

/********************************************************/
/*  EVENT HANDLERS AND METHODS TO STORE A NEW ROUTE     */
/*  AND RETRIEVE STORES ROUTES AND DISPLAY ON MAP       */
/********************************************************/

// Method to retrieve trail form data and map data from 
// MapBox GL JS object
$('#new-trail').on('submit', async function(e) {
  e.preventDefault();
  const form = document.querySelector('#new-trail');
  const user_id = form.dataset.userid;
  console.log('user_id: ', user_id);

  let name = $('#trail').val();
  console.log('Input Name', name);
  const distance = JSON.parse(localStorage.getItem('distance'));
  const duration = JSON.parse(localStorage.getItem('duration'));
  const coordinates = JSON.parse(localStorage.getItem('coords')).coordinates;
  const package = {
      "name": name,
      "distance": distance,
      "duration": duration, 
      "coordinates": coordinates
  }
  console.log(package);

  const response = await axios.post(`${URL}/users/${user_id}/trails`, package);
  console.log(response); 
  location.reload(true); 
})

// Method to retrieve a Stored  User route 
// and display on the Map if no errors
$('#trail-list').on('click', '#view-btn' , async function(e) {
  
  const user_id = $(e.target).data('userid');
  const trail_id = $(e.target).data('trailid');
  console.log(`REQUEST URL: ${URL}/users/${user_id}/trails/${trail_id}`);
  
  const response = await axios.get(`${URL}/users/${user_id}/trails/${trail_id}`);

  console.log('RESPONSE: ', response);
  drawStoredMap(response);
})

// Checks for errors on the reponse and preps coordinates for display
// Calls add route function
function drawStoredMap(resp) {
    
  // Check for errors and display
  if (resp.data.errors) {
      errs = resp.data.errors;
      errs.forEach( err => 
          { Object.entries(err).forEach(([key, value]) => 
              { 
                  console.log(`${key} : ${value}`);
                  $(`#${key}-err`).text(value);
              })
          })
  }
  // If error free, redraw map
  const coords = {
      coordinates: resp.data.maproute.coordinates,
      type: "LineString"
  }

  console.log("COORDS: ", coords);
  addRoute(coords);      
}

