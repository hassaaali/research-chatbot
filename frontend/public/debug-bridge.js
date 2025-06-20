(function(){
  const send = (type, payload) => {
    window.parent.postMessage({ __operative_debug: true, type, payload }, '*');
  };
  ['log','info','warn','error','debug'].forEach(level=>{
    const orig = console[level] ? console[level].bind(console) : console.log.bind(console);
    console[level] = (...args) => {
      send('console', { level, args });
      orig(...args);
    };
  });
  const origFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    send('network', { kind:'fetch', phase:'request', args });
    try {
      const res = await origFetch(...args);
      send('network', { kind:'fetch', phase:'response', url: res.url, status: res.status });
      return res;
    } catch (err) {
      send('network', { kind:'fetch', phase:'error', error: String(err) });
      throw err;
    }
  };
  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...rest){
    send('network', { kind:'xhr', phase:'request', method, url });
    this.addEventListener('load', () => {
      send('network', { kind:'xhr', phase:'response', url, status: this.status });
    });
    return origOpen.call(this, method, url, ...rest);
  };

  // Capture uncaught JS errors
  window.addEventListener('error', (event) => {
    send('console', { level: 'error', args: [event.message, event.filename + ':' + event.lineno + ':' + event.colno] });
  });

  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    send('console', { level: 'error', args: ['Unhandled promise rejection:', event.reason] });
  });

})();