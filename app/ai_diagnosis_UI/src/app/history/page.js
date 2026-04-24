'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Spin } from 'antd';
import { auth, firebaseAuthEnabled } from '@/firebase.config';

export default function HistoryPage() {
  const [profiles, setProfiles] = useState([]);
  const [filteredProfiles, setFilteredProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    Ear: false,
    Nose: false,
    Throat: false,
  });
  const router = useRouter();

  const fetchProfiles = async () => {
    try {
      if (!firebaseAuthEnabled || !auth?.currentUser) {
        setProfiles([]);
        setFilteredProfiles([]);
        setLoading(false);
        return;
      }

      const token = await auth.currentUser.getIdToken();
      const response = await fetch('/api/history', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();
      if (data.profiles) {
        setProfiles(data.profiles);
        setFilteredProfiles(data.profiles);
      } else {
        setProfiles([]);
        setFilteredProfiles([]);
      }
    } catch (error) {
      console.error('Error fetching profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  useEffect(() => {
    const filtered = profiles.filter((profile) => {
      const matchesSearch = profile.name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilters = Object.keys(filters).some(
        (key) => filters[key] && profile.category?.includes(key)
      );

      return matchesSearch && (matchesFilters || !Object.values(filters).some(Boolean));
    });

    setFilteredProfiles(filtered);
  }, [filters, profiles, searchTerm]);

  const handleProfileClick = (profileId) => {
    router.push(`/profile/${profileId}`);
  };

  const handleFilterChange = (filter) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filter]: !prevFilters[filter],
    }));
  };

  return (
    <div className="min-h-screen p-4 mt-20">
      <div className="mx-auto grid max-w-screen-lg grid-cols-10 gap-4">
        <div className="col-span-3 rounded-lg border border-gray-300 bg-gray-100 p-4">
          {!firebaseAuthEnabled && (
            <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
              History is unavailable because authentication is disabled.
            </div>
          )}

          <h3 className="mb-4 text-lg font-semibold">Filters</h3>
          <input
            type="text"
            placeholder="Search..."
            className="mb-4 w-full rounded-lg border border-gray-300 p-2"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="flex flex-col space-y-2">
            {Object.keys(filters).map((filter) => (
              <label key={filter} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters[filter]}
                  onChange={() => handleFilterChange(filter)}
                />
                <span>{filter}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="col-span-7 rounded-lg border border-gray-300 bg-gray-50 p-4">
          {loading ? (
            <div className="flex h-full items-center justify-center">
              <Spin size="large" />
            </div>
          ) : filteredProfiles.length > 0 ? (
            <ul className="space-y-4">
              {filteredProfiles.map((profile) => (
                <li
                  key={profile._id}
                  className="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow transition hover:bg-gray-100"
                  onClick={() => handleProfileClick(profile._id)}
                >
                  <div className="mb-2 text-gray-500">
                    Created on: {new Date(profile.createdAt).toLocaleDateString()}
                  </div>
                  <div className="flex space-x-4">
                    {profile.images.map((image, index) => (
                      <img
                        key={index}
                        src={image.path}
                        alt={`image-${index}`}
                        className="h-24 w-24 rounded-lg object-cover"
                      />
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No profiles found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
