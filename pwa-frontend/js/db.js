// js/db.js
const DB_NAME = 'AshaVaniDB';
const DB_VERSION = 1;
const STORE_NAME = 'offline_logs';

let db;

// Initialize the Database
const initDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = (event) => reject('Database error: ' + event.target.errorCode);

    request.onupgradeneeded = (event) => {
      db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
        console.log('[IndexedDB] Object store created');
      }
    };

    request.onsuccess = (event) => {
      db = event.target.result;
      console.log('[IndexedDB] Database initialized successfully');
      resolve(db);
    };
  });
};

// Save a patient record offline
const saveLogOffline = (record) => {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    
    record.timestamp = new Date().toISOString();
    record.synced = false;
    
    const request = store.add(record);
    request.onsuccess = () => resolve('Record saved offline!');
    request.onerror = () => reject('Error saving record');
  });
};