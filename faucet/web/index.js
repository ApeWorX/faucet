function transfer(address) {
  fetch(`${window.location.origin}/transfer/${address}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        const errorDiv = document.getElementById('error-response');
        console.log(`Error: ${data.error}`);
        errorDiv.innerHTML = `
          <pre>
            "ERROR": ${data.error}
          </pre>
      `} 
      else {
        const responseDiv = document.getElementById('faucet-response');
        responseDiv.innerHTML = `
          <pre>
            "txn_hash": ${data.txn_hash}
            "balance": ${data.balance}
          </pre>
        `;
      }
    })
    .catch(error => {
      console.log(`Error: ${error.message}`);
    });
}

function callFaucet(event) {
  event.preventDefault();
  const addressInput = document.getElementById('faucet-request');
  const address = addressInput.value;

  transfer(address);
}
