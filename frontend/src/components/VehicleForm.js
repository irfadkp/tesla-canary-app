import React, { useState } from 'react';
import axios from 'axios';
import { logHeavily, logError, logSuccess } from '../utils/logger';
import './VehicleForm.css';

const VehicleForm = ({ onError }) => {
  const [formData, setFormData] = useState({
    model: '',
    type: 'Sports',
    price: '',
    color: '',
    year: 2024,
    inStock: true
  });
  const [submitting, setSubmitting] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    console.log('Form field changed:', name, '=', type === 'checkbox' ? checked : value);
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    logHeavily('Submitting vehicle form');
    console.log('========================================');
    console.log('FORM SUBMISSION');
    console.log('========================================');
    console.log('Form data:', formData);
    console.log('Timestamp:', new Date().toISOString());
    console.log('========================================');
    
    setSubmitting(true);
    
    try {
      const startTime = performance.now();
      const response = await axios.post(`${API_URL}/api/vehicles`, formData);
      const duration = performance.now() - startTime;
      
      console.log('Vehicle created successfully');
      console.log('Response:', response.data);
      console.log('Response time:', duration, 'ms');
      console.log('Status:', response.status);
      
      logSuccess('Vehicle created successfully');
      
      // Reset form
      setFormData({
        model: '',
        type: 'Sports',
        price: '',
        color: '',
        year: 2024,
        inStock: true
      });
      
      alert('Vehicle created successfully!');
    } catch (error) {
      console.error('========================================');
      console.error('FORM SUBMISSION ERROR');
      console.error('========================================');
      console.error('Error:', error.message);
      console.error('Response:', error.response?.data);
      console.error('Status:', error.response?.status);
      console.error('========================================');
      
      logError('Failed to create vehicle', error);
      onError();
      alert('Failed to create vehicle. Check console for details.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="vehicle-form">
      <h2>Add New Vehicle</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Model:</label>
          <input
            type="text"
            name="model"
            value={formData.model}
            onChange={handleChange}
            required
            placeholder="e.g., 488 GTB, F8 Tributo"
          />
        </div>

        <div className="form-group">
          <label>Type:</label>
          <select name="type" value={formData.type} onChange={handleChange}>
            <option value="Sports">Sports</option>
            <option value="SUV">SUV</option>
            <option value="Sports">Sports</option>
            <option value="Sedan">Sedan</option>
          </select>
        </div>

        <div className="form-group">
          <label>Price:</label>
          <input
            type="number"
            name="price"
            value={formData.price}
            onChange={handleChange}
            required
            min="0"
            placeholder="e.g., 45000"
          />
        </div>

        <div className="form-group">
          <label>Color:</label>
          <input
            type="text"
            name="color"
            value={formData.color}
            onChange={handleChange}
            required
            placeholder="e.g., Blue, Red"
          />
        </div>

        <div className="form-group">
          <label>Year:</label>
          <input
            type="number"
            name="year"
            value={formData.year}
            onChange={handleChange}
            required
            min="2020"
            max="2025"
          />
        </div>

        <div className="form-group checkbox">
          <label>
            <input
              type="checkbox"
              name="inStock"
              checked={formData.inStock}
              onChange={handleChange}
            />
            In Stock
          </label>
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating...' : 'Create Vehicle'}
        </button>
      </form>
    </div>
  );
};

export default VehicleForm;
