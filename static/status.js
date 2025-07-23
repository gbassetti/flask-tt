var timeout;
  
  async function getStatus() {
  
    let get;
    
    try {
      const res = await fetch("/status");
      get = await res.json();
    } catch (e) {
      console.error("Error: ", e);
    }
    
    document.getElementById("innerCurrent").innerHTML = get.current;
    document.getElementById("innerTotalAthletes").innerHTML = get.total;
    document.getElementById("innerUploaded").innerHTML = get.uploaded;
    
    
    if (get.current == get.total && get.current > 0){
      document.getElementById("innerCurrent").innerHTML += " All";
      clearTimeout(timeout);
      return false;
    }
     
    timeout = setTimeout(getStatus, 1000);
  }
  
  getStatus();
