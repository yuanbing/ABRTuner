var fs = require('fs');
var Chrome = require('chrome-remote-interface');
var duration;
var trace_name;
var trace_array_bw = [];
var trace_array_duration = [];
var scheme;
var main_html;
process.argv.forEach(function (val, index, array) {
    if(index === 2) {
        trace_name = val;
    }
    if(index === 3) {
        scheme = val;
    }
}); 
console.log("trace name = "+trace_name)

fs.readFileSync(trace_name).toString().split('\n').forEach(function (line) { 
	var temp_bw = Number(line.split(" ")[1]);
	var temp_duration = Number(line.split(" ")[0]);
	
	//console.log(Number(line.split(" ")[0])+" "+Number(line.split(" ")[1]));

	if (trace_array_bw.length==0) {
		trace_array_bw.push(temp_bw);
		trace_array_duration.push(temp_duration);
	}
	
	if (line.split(" ")[1]!=undefined){
		trace_array_bw.push(temp_bw);
		trace_array_duration.push(temp_duration);
	}
	
})

//console.log(trace_array_bw)

Chrome(function (chrome) {
    with (chrome) {
	var cnt=0;
        Network.canEmulateNetworkConditions().catch(function () {
            console.log("Do not support network emulation!");
        });
        Network.canClearBrowserCache().catch(function () {
            console.log("Do not support cache clear!");
        });
		
	Network.enable();
	Network.emulateNetworkConditions({offline: false, latency: 0, downloadThroughput: 100*trace_array_bw[cnt], uploadThroughput: 100*trace_array_bw[cnt]});
	cnt+=1
		
	var timer;
	Network.clearBrowserCache();		
		
	timer = setInterval(myBandwidthEmulation, 1000);
	function myBandwidthEmulation(){
		Network.emulateNetworkConditions({offline: false, latency: 0, downloadThroughput: 100*trace_array_bw[cnt], uploadThroughput: 100*trace_array_bw[cnt]});
		cnt = cnt+1;
	}
        
        
        Page.enable();
		if (scheme=="dash"){
			main_html = "http://68.181.99.194/yz_index.html.en.dash"
		}
		else if (scheme=="mpc"){
			main_html = "http://68.181.99.194/yz_index.html"
		}
		else if (scheme=="hyb"){
			main_html = "http://68.181.99.194/yz_index.html.en.hyb"
		}
		else if(scheme=="tuner"){
			main_html = "http://68.181.99.194/yz_index.html.en.tuner"
		}
                else if(scheme=="pensieve"){
                        main_html = "http://68.181.99.194/yz_index.html.en.pensieve"
			//main_html = "http://68.181.99.194/myindex_RL.html"
                }
		else{
			main_html = "http://68.181.99.194/yz_index.html.en"
		}
		console.log("Scheme is "+ main_html)
        Page.navigate({'url': main_html});

	Network.requestWillBeSent(function (params) {
    		console.log(params.request.url);
    		if (params.request.url.match(/49.m4s/)) {
                        console.log("Yun Final : Timeout - End experiment");
        		close();
                        process.exit();
    		}
	});

//        setTimeout(function () {
//            console.log("Yun Final : Timeout - End experiment");
//			close();
//			process.exit();
//        }, 600000);
   }
}).on('error', function () {
    console.error('Cannot connect to Chrome');
});