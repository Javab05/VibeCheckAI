import Constants from 'expo-constants';

const host = Constants.expoConfig?.hostUri?.split(':')[0] ?? 'localhost';
export const API_URL = `http://${host}:5000`;