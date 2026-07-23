/**
 * @author Benjamin Jakimow, Humboldt-Universität zu Berlin, Geomatics Lab, 2013
 * 
 * 
 */

    function initDocument(ReportIDs){
    	if(typeof ReportIDs === 'undefined'){
    		showAllReports();
	    } else {
	    	focusReport(ReportIDs);
	    }
    	
    }

  	function focusReport(ReportIDs){
  		var reports = document.getElementsByClassName('report');
  		document.getElementById('NavLink_showAll').style.fontWeight = "normal";
  		
  		var reportIDs;
  		if(ReportIDs instanceof Array){
  			reportIDs = ReportIDs;
  		}else{
  			reportIDs = [ReportIDs];
  		}
  		
  		for (i=0; i < reports.length; i++) {
  			report = reports[i];
  			
  			if(reportIDs.indexOf(report.id) != -1){
  				document.getElementById(report.id).style.display = "block";
  				document.getElementById('NavLink_'+report.id).style.fontWeight = "bold";
  				
  			} else {
				document.getElementById(report.id).style.display = "none";
				document.getElementById('NavLink_'+report.id).style.fontWeight = "normal";  
			}	
  		}	
  	}
  	
  	function showAllReports(){
  		var reports = document.getElementsByClassName('report');
  		for (i=0; i < reports.length; i++) {
  			report = reports[i];
  			report.style.display = "block";
  			document.getElementById('NavLink_'+report.id).style.fontWeight = "normal";	
  		}
  		document.getElementById('NavLink_showAll').style.fontWeight = "bold";
  	}
  	
