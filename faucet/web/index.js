function transfer(address) {
  const responseDiv = document.getElementById('faucet-response');
  const errorDiv = document.getElementById('error-response');
  responseDiv.innerHTML = "";
  errorDiv.innerHTML = "";

  if (address === "") {
    errorDiv.innerHTML = "<pre>ERROR: Must provide an address or ENS</pre>";
  } else {
    fetch(`${window.location.origin}/transfer/${address}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        } else {
          responseDiv.innerHTML = `
            <pre>
              Transaction: ${data.txn_hash}
              Your balance is now: ${data.balance}
            </pre>
          `;
        }
      })
      .catch(error => {
        errorDiv.innerHTML = `<pre>ERROR: ${error.message}</pre>`;
      });
  }
}

function callFaucet(event) {
  event.preventDefault();
  const addressInput = document.getElementById('faucet-request');
  const address = addressInput.value;

  transfer(address);
}
