function transfer(address) {
  fetch(`http://127.0.0.1:8000/transfer/${address}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.log(`Error: ${data.error}`);
      } else {
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

function callFaucet() {
  const addressInput = document.getElementById('faucet-request');
  const address = addressInput.value;

  transfer(address);
}
