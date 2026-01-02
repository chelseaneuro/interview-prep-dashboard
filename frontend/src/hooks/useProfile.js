import { useState, useEffect } from 'react';
import profileService from '../services/profileService';

export function useProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadProfile = async () => {
    try {
      const data = await profileService.getProfile();
      setProfile(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
    const interval = setInterval(loadProfile, 30000);
    return () => clearInterval(interval);
  }, []);

  return { profile, loading, error, refresh: loadProfile };
}
