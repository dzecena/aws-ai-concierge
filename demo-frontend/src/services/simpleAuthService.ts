// Simple authentication service without AWS dependencies
export const simpleAuthService = {
  login: (username: string, password: string): boolean => {
    return username === 'demo.judge@example.com' && password === 'OqN#ldMRn5TfA@Kw';
  },
  
  logout: (): void => {
    // Simple logout
  },
  
  isAuthenticated: (): boolean => {
    // Simple check
    return false;
  }
};