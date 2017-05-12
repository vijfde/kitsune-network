function openModal(innerHTML) {
  document.getElementById('modal_content').innerHTML = innerHTML;
  document.getElementById('modal').style.display = "block";
}

function closeModal() {
  document.getElementById('modal').style.display = "none";
}

var map, newPinMarker, markerInfoWindow;

function initMap() {

  showLoadingIndicator();
  var japan = {lat: 36.2048, lng: 138.2529};
  map = new google.maps.Map(document.getElementById('map'), {
    zoomControl: true,
    mapTypeControl: false,
    scaleControl: false,
    streetViewControl: false,
    rotateControl: false,
    fullscreenControl: true,
    center: japan,
    zoom: 5,
    styles:
     [{"elementType":"geometry","stylers":[{"color":"#212121"}]},{"elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"elementType":"labels.text.fill","stylers":[{"color":"#757575"}]},{"elementType":"labels.text.stroke","stylers":[{"color":"#212121"}]},{"featureType":"administrative","elementType":"geometry","stylers":[{"color":"#757575"}]},{"featureType":"administrative.country","elementType":"labels.text.fill","stylers":[{"color":"#9e9e9e"}]},{"featureType":"administrative.land_parcel","stylers":[{"visibility":"off"}]},{"featureType":"administrative.locality","elementType":"labels.text.fill","stylers":[{"color":"#bdbdbd"}]},{"featureType":"administrative.neighborhood","stylers":[{"visibility":"off"}]},{"featureType":"poi","elementType":"labels.text","stylers":[{"visibility":"off"}]},{"featureType":"poi","elementType":"labels.text.fill","stylers":[{"color":"#757575"}]},{"featureType":"poi.business","stylers":[{"visibility":"off"}]},{"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#181818"}]},{"featureType":"poi.park","elementType":"labels.text.fill","stylers":[{"color":"#616161"}]},{"featureType":"poi.park","elementType":"labels.text.stroke","stylers":[{"color":"#1b1b1b"}]},{"featureType":"road","elementType":"geometry.fill","stylers":[{"color":"#c50000"}]},{"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#c50000"}]},{"featureType":"road","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"labels.text.fill","stylers":[{"color":"#8a8a8a"}]},{"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#373737"}]},{"featureType":"road.arterial","elementType":"geometry.fill","stylers":[{"color":"#c50000"}]},{"featureType":"road.arterial","elementType":"geometry.stroke","stylers":[{"color":"#c50000"}]},{"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#3c3c3c"}]},{"featureType":"road.highway","elementType":"geometry.fill","stylers":[{"color":"#c50000"}]},{"featureType":"road.highway","elementType":"geometry.stroke","stylers":[{"color":"#c50000"}]},{"featureType":"road.highway.controlled_access","elementType":"geometry","stylers":[{"color":"#4e4e4e"}]},{"featureType":"road.highway.controlled_access","elementType":"geometry.fill","stylers":[{"color":"#c50000"}]},{"featureType":"road.highway.controlled_access","elementType":"geometry.stroke","stylers":[{"color":"#c50000"}]},{"featureType":"road.local","elementType":"geometry.fill","stylers":[{"color":"#c50000"}]},{"featureType":"road.local","elementType":"geometry.stroke","stylers":[{"color":"#c50000"}]},{"featureType":"road.local","elementType":"labels.text.fill","stylers":[{"color":"#616161"}]},{"featureType":"transit","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"labels.text.fill","stylers":[{"color":"#757575"}]},{"featureType":"water","elementType":"geometry","stylers":[{"color":"#000000"}]},{"featureType":"water","elementType":"labels.text","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#3d3d3d"}]}]
  });
  var mapLoadListener = map.addListener('tilesloaded', function() {
    hideLoadingIndicator();
    google.maps.event.removeListener(mapLoadListener);
  });

  setupBottomCenterControl(map);
  var logoDiv = document.createElement('div');
  logoDiv.innerHTML = "<img id='logoImg' src='/images/logo.png' />";
  map.controls[google.maps.ControlPosition.TOP].push(logoDiv);

  // get and setup markers
  var url = '/pins.json';
  if (document.getElementById('shouldForceRefreshPins')) {
    url += '?forceRefresh=True';
  }
  ajax({
    method: 'GET',
    relativeURL: url,
    dataType: 'JSON',
    success: setupMarkers,
    error: function() {
      // There was a connection error of some sort
    }
  });

  // Try HTML5 geolocation.
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      map.setCenter(pos);
    }, function() {
      // User probbaly did not give permission for their location
    });
  } else {
    // Browser doesn't support Geolocation
  }

}

function setupMarkers(json) {
  json.forEach(function(pin) {
    var location = {lat: pin.lat, lng: pin.lng};
    var image = {
      url: '/images/pins/' + pin.icon + '.png',
      size: new google.maps.Size(35, 60),
      anchor: new google.maps.Point(35 / 2, 60 / 2)
    };
    var marker =  new google.maps.Marker({
      position: location,
      icon: image,
      map: map,
    });
    marker.addListener('click', function() {
      showPinInfoWindow(pin, marker);
    });
  });
}

function showPinInfoWindow(pin, marker) {
  ajax({
    method: 'GET',
    relativeURL: '/pin/' + pin.id,
    dataType: 'HTML',
    success: function(html) {
      if (markerInfoWindow !== undefined) {
        markerInfoWindow.close()
      }
      markerInfoWindow = new google.maps.InfoWindow({
        content: html
      })
      markerInfoWindow.open(map, marker);
    },
    error: function() {
      // There was a connection error of some sort
    }
  });
}

function setupBottomCenterControl(map) {

  var controlDiv = document.createElement('div');
  controlDiv.style['padding-bottom'] = '10px';
  controlDiv.style.clear = 'both';

  var addPinUI = document.createElement('div');
  addPinUI.id = 'addPinUI';
  controlDiv.appendChild(addPinUI);
  var addPinText = document.createElement('div');
  addPinText.id = 'addPinText';
  var addPinTextLabel = document.getElementById('addPinTextLabel');
  addPinText.innerHTML = addPinTextLabel.innerHTML;
  addPinUI.appendChild(addPinText);

  var showAboutUI = document.createElement('div');
  showAboutUI.id = 'showAboutUI';
  controlDiv.appendChild(showAboutUI);
  var showAboutText = document.createElement('div');
  showAboutText.id = 'showAboutText';
  var showAboutTextLabel = document.getElementById('showAboutTextLabel');
  showAboutText.innerHTML = showAboutTextLabel.innerHTML;
  showAboutUI.appendChild(showAboutText);

  addPinUI.addEventListener('click', function() {
    if (newPinMarker !== undefined) {
      newPinMarker.setMap(null);
    }
    newPinMarker = new google.maps.Marker({
      position: map.getCenter(),
      map: map,
      animation: google.maps.Animation.DROP,
      draggable:true
    });
    if (markerInfoWindow !== undefined) {
      markerInfoWindow.close()
    }
    markerInfoWindow = new google.maps.InfoWindow({
      content: document.getElementById('newPinMessage').innerHTML
    })
    google.maps.event.addListener(markerInfoWindow, 'closeclick', function() {
      newPinMarker.setMap(null);
    });
    markerInfoWindow.open(map, newPinMarker);
    document.getElementById('newPinMessage').style.display = "block";
  });

  showAboutUI.addEventListener('click', function() {
    openModal(document.getElementById('aboutContent').innerHTML);
    var languageSelector = document.getElementById("languageSelector");
    languageSelector.addEventListener("input", function () {
      document.cookie = "language=" + languageSelector.value;
      location.reload();
    });
  });

  map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(controlDiv);

}

function setupPinInputRadios() {
  var pinInputs = document.querySelectorAll(".pin-input");
  Array.prototype.forEach.call(pinInputs, function(el, i){
    var pinInput = el.querySelectorAll("img")[0];
    var pinRadio = el.querySelectorAll("input")[0];
    pinInput.addEventListener("click", function() {
      pinRadio.checked = true;
    });
  });
}

function openModalForm() {
  ajax({
    method: 'GET',
    relativeURL: '/new_pin_form.html',
    dataType: 'HTML',
    success: function(html) {
      openModal(html);
      setupPinInputRadios();
      var inputs = document.querySelectorAll("input, select, textarea");
      Array.prototype.forEach.call(inputs, function(el, i){
        el.addEventListener("input", function () {
          var className = "has-error";
          if (el.value.length > 0) {
            className = "has-success";
          }
          if (el.type == "email") {
            if (validateEmail(el.value)) {
              className = "has-success";
            } else {
              className = "has-warning";
            }
          }
          var parent = el.parentNode;
          parent.classList.remove("has-warning");
          parent.classList.remove("has-error");
          parent.classList.remove("has-success");
          parent.classList.add(className);
        });
      });
    },
    error: function() {
      // There was a connection error of some sort
    }
  });
}

function validateEmail(email) {
    var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

function getFormValue(elementID) {
  var element = document.getElementById(elementID);
  if (element != null) {
    return element.value;
  } else {
    return "";
  }
}

function getPinFormData() {
  var data = new QueryStringBuilder();
  data.add("name", document.getElementById('inputName').value);
  data.add("about_you", document.getElementById('inputAboutYou').value);
  data.add("email", getFormValue('inputEmail'));
  data.add("favorite_member", document.getElementById('inputFavMember').value);
  data.add("favorite_song", document.getElementById('inputFavSong').value);
  data.add("editAccessUUID", getFormValue('editAccessUUIDinput'));
  data.add("communities", getSelectValues(document.getElementById('inputCommunities')));
  if (newPinMarker !== undefined) {
    var latlng = newPinMarker.getPosition();
    data.add("latitude", latlng.lat());
    data.add("longitude", latlng.lng());
  }

  var pinRadios = document.getElementsByName('inputPinIcon');
  for (var i = 0, length = pinRadios.length; i < length; i++) {
      if (pinRadios[i].checked) {
          data.add("pin_icon", pinRadios[i].value);
          break;
      }
  }
  return data;
}

function submitNewPinForm() {
  var data = getPinFormData();
  ajax({
    method: 'POST',
    relativeURL: '/pin',
    dataType: 'HTML',
    data: data,
    success: function(html) {
      markerInfoWindow.close();
      newPinMarker.setMap(null);
      openModal(html);
    },
    error: function(html) {
      var formErrorElement = document.getElementById("formError");
      formErrorElement.innerHTML = html
    }
  });
}

function submitEditPinForm() {
  var data = getPinFormData();
  ajax({
    method: 'PUT',
    relativeURL: '/pin',
    dataType: 'HTML',
    data: data,
    success: function(html) {
      openModal(html);
    },
    error: function(html) {
      var formErrorElement = document.getElementById("formError");
      formErrorElement.innerHTML = html
    }
  });
}

function submitEditPinEmail() {
  var data = new QueryStringBuilder();
  data.add("email", document.getElementById('inputEditEmail').value);

  ajax({
    method: 'POST',
    relativeURL: '/pin/editRequest',
    dataType: 'HTML',
    data: data,
    success: function(html) {
      openModal(html);
    },
    error: function(html) {
      // There was a connection error of some sort
    }
  });

}


function getSelectValues(select) {
  var result = [];
  var options = select && select.options;
  var opt;

  for (var i=0, iLen=options.length; i<iLen; i++) {
    opt = options[i];

    if (opt.selected) {
      result.push(opt.value || opt.text);
    }
  }
  return result;
}

function QueryStringBuilder() {
  var nameValues = [];
  this.add = function(name, value) {
    nameValues.push( {name: name, value: value} );
  };
  this.toQueryString = function() {
    var segments = [], nameValue;
    for (var i = 0, len = nameValues.length; i < len; i++) {
        nameValue = nameValues[i];
        segments[i] = encodeURIComponent(nameValue.name) + "=" + encodeURIComponent(nameValue.value);
    }
    return segments.join("&");
  };
}

var loadingCount = 0;
function showLoadingIndicator() {
  loadingCount += 2;// once for actual show and once for min show timer
  var loadingImage = document.getElementById("loadingImage");
  loadingImage.style.display = "block";
  window.setTimeout(hideLoadingIndicator, 250);
}

function hideLoadingIndicator() {
  loadingCount--;
  if (loadingCount > 0) { return }
  var loadingImage = document.getElementById("loadingImage");
  loadingImage.style.display = "none";
}

function ajax(settings) {
  showLoadingIndicator();
  var request = new XMLHttpRequest();
  request.open(settings.method, settings.relativeURL, true);
  if (settings.method == 'POST' || settings.method == 'PUT') {
    request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
  }
  request.onload = function() {
    if (request.status >= 200 && request.status < 400) {
      if (settings.dataType == "JSON") {
        var json = JSON.parse(request.responseText);
        settings.success(json)
      } else {
        settings.success(request.responseText)
      }
    } else {
      // We reached our target server, but it returned an error
      settings.error(request.responseText);
    }
    hideLoadingIndicator();
  };
  request.onerror = function() {
    settings.error("");
    hideLoadingIndicator();
  };
  if (settings.method == 'POST' || settings.method == 'PUT') {
    request.send(settings.data.toQueryString());
  } else {
    request.send();
  }
}
