

test_page="""
<html>
    <head>
        <script src="/execute/execute.js"></script>
        <script>
        const main = async () =>
        {
            let loc = window.location;
            exe = new Executor(`ws://${loc.host}/execute`)
            await exe.connect();
            let fxns = await exe.show();
            for(fxn in fxns)
            {
                let div = document.querySelector("div#fxndiv");
                div.appendChild(document.createTextNode(fxn));
                div.appendChild(document.createElement("BR"));
                console.log(`fxn = ${fxn}`);
            }
            useless = await exe.do_something();
            console.log(useless);
        }
        </script>
    </head>
    <body onload='main()'>

    <div id="fxndiv"></div>
    </body>
</html>
"""

javascript = """
const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay))
function Queue()
{
	this.elements = [];
}

Queue.prototype.empty =function()
{
	return this.elements.length == 0;
}

Queue.prototype.put = function(item)
{
	this.elements.push(item);
}

Queue.prototype.get = async function()
{
	while(1)
	{
		if(this.elements.length > 0)
			return this.elements.shift();
		await sleep(250);
	}
}


function Executor(uri)
{
	if(uri === undefined)
		this.uri = "ws://fields.mmto.arizona.edu:65000/execute"
	else
		this.uri = uri;
}

Executor.prototype.connect = async function()
{
	this.ws = new WebSocket(this.uri);
	let myself = this;
	
	await new Promise(
		function(resolve, reject) 
		{
			myself.ws.onopen = function(evt)
			{
				resolve(evt);
			};
			
			myself.ws.onerror = function(evt)
			{
				reject(evt);
			};

		});
	
	this.info = await this.execute("show", {});
	for(let cmd in this.info)
	{
		this[cmd] = function()
		{
			let args = {};
			for( ii in arguments)
			{
				let argname = this.info[cmd]['args'][ii]["name"];
				args[argname] = arguments[ii];
			}
			return this.execute(cmd, args);
			
		}
	}
}

Executor.prototype.read = function(evt)
{
	let ws = this.ws;
	return new Promise(
		function(resolve, error)
		{
			ws.onmessage = function(msg)
			{
				resolve(msg);
			}
		});
}

Executor.prototype.execute = async function(cmd, args)
{
	let payload = {cmd:cmd, args:args};
	this.ws.send(JSON.stringify(payload));
	let resp = await this.read();
	this.last_response = resp;
	return JSON.parse(resp["data"])["return"];
}

"""
