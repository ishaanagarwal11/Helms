const express = require('express');
const mysql = require('mysql2');       // or 'mysql'
const amqp = require('amqplib/callback_api'); // for RabbitMQ

const app = express();
const port = 8080;

// Read environment variables (provided by K8s)
const DB_HOST = process.env.DB_HOST || "db-service";
const DB_USER = process.env.DB_USER || "root";
const DB_PASS = process.env.DB_PASS || "MySuperSecret";
const DB_NAME = process.env.DB_NAME || "testdb";
const QUEUE_HOST = process.env.QUEUE_HOST || "queue-service";

// Basic route
app.get('/', (req, res) => {
  res.send("Hello from the backend!");
});

// Health endpoints
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

app.get('/ready', (req, res) => {
  // You could add logic to test if DB or queue are reachable
  res.status(200).send('READY');
});

// Connect to MySQL (this may fail if MySQL is not reachable)
const db = mysql.createConnection({
  host: DB_HOST,
  user: DB_USER,
  password: DB_PASS,
  database: DB_NAME
});

// Just a test query
app.get('/db-test', (req, res) => {
  db.query('SELECT NOW() as now', (err, rows) => {
    if (err) {
      return res.status(500).send(`DB Error: ${err.message}`);
    }
    res.send(rows);
  });
});

let memEater = [];
for (let i = 0; i < 1e7; i++) {
  memEater.push(i);
}

// Connect to RabbitMQ
// This will show us errors in logs if the queue is unreachable or misconfigured
amqp.connect(`amqp://${QUEUE_HOST}`, (err, connection) => {
  if (err) {
    console.error("Failed to connect to RabbitMQ:", err.message);
  } else {
    console.log("Connected to RabbitMQ successfully");
    connection.close();
  }
});

app.listen(port, () => {
  console.log(`Backend listening on port ${port}`);
});
