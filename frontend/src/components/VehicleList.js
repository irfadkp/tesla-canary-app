import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { logHeavily, logError, logSuccess } from '../utils/logger';
import './VehicleList.css';

const VehicleList = ({ onError }) => {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState('');

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

  useEffect(() => {
    fetchVehicles();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      console.log('[AUTO-REFRESH] Fetching vehicles...');
      fetchVehicles();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchVehicles = async () => {
    logHeavily('Fetching vehicles from API');
    console.log('API URL:', `${API_URL}/api/vehicles`);
    console.log('Timestamp:', new Date().toISOString());
    
    setLoading(true);
    
    try {
      const startTime = performance.now();
      const response = await axios.get(`${API_URL}/api/vehicles`);
      const duration = performance.now() - startTime;
      
      console.log('Response received:', response.status);
      console.log('Response time:', duration, 'ms');
      console.log('Vehicles count:', response.data.length);
      console.log('Response data:', response.data);
      
      setVehicles(response.data);
      logSuccess(`Successfully fetched ${response.data.length} vehicles`);
    } catch (error) {
      console.error('========================================');
      console.error('ERROR FETCHING VEHICLES');
      console.error('========================================');
      console.error('Error message:', error.message);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('========================================');
      
      logError('Failed to fetch vehicles', error);
      onError();
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchType) {
      fetchVehicles();
      return;
    }

    logHeavily(`Searching vehicles by type: ${searchType}`);
    setLoading(true);
    
    try {
      const response = await axios.get(`${API_URL}/api/vehicles/search`, {
        params: { type: searchType }
      });
      
      console.log('Search results:', response.data.length);
      setVehicles(response.data);
      logSuccess(`Found ${response.data.length} vehicles`);
    } catch (error) {
      logError('Search failed', error);
      onError();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    logHeavily(`Deleting vehicle: ${id}`);
    
    try {
      await axios.delete(`${API_URL}/api/vehicles/${id}`);
      console.log('Vehicle deleted successfully:', id);
      logSuccess(`Deleted vehicle ${id}`);
      fetchVehicles();
    } catch (error) {
      logError('Delete failed', error);
      onError();
    }
  };

  return (
    <div className="vehicle-list">
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by type (Sports, SUV, Sports)..."
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
        <button onClick={fetchVehicles}>Refresh</button>
      </div>

      {loading && <div className="loading">Loading vehicles...</div>}

      <div className="vehicle-grid">
        {vehicles.map((vehicle) => (
          <div key={vehicle.id} className="vehicle-card">
            <h3>{vehicle.model}</h3>
            <p><strong>Type:</strong> {vehicle.type}</p>
            <p><strong>Price:</strong> ${vehicle.price?.toLocaleString()}</p>
            <p><strong>Color:</strong> {vehicle.color}</p>
            <p><strong>Year:</strong> {vehicle.year}</p>
            <p><strong>In Stock:</strong> {vehicle.inStock ? '✓ Yes' : '✗ No'}</p>
            <button 
              className="delete-btn"
              onClick={() => handleDelete(vehicle.id)}
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      {!loading && vehicles.length === 0 && (
        <div className="no-vehicles">No vehicles found</div>
      )}
    </div>
  );
};

export default VehicleList;
