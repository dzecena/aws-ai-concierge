import { Amplify } from '@aws-amplify/core';
import { signIn as amplifySignIn, signOut as amplifySignOut, getCurrentUser, confirmSignIn } from '@aws-amplify/auth';
import { awsConfig } from '../config/aws-config';
import { User } from '../types';

// Configure Amplify
Amplify.configure(awsConfig);

class AuthService {
  private currentUserChallenge: any = null;

  async signIn(username: string, password: string) {
    try {
      const result = await amplifySignIn({
        username,
        password,
      });

      if (result.isSignedIn) {
        return result;
      }

      // Handle challenges (like NEW_PASSWORD_REQUIRED)
      if (result.nextStep) {
        this.currentUserChallenge = result;
        return result;
      }

      throw new Error('Sign in failed');
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  }

  async completeNewPassword(newPassword: string) {
    try {
      if (!this.currentUserChallenge) {
        throw new Error('No pending password challenge');
      }

      const result = await confirmSignIn({
        challengeResponse: newPassword,
      });

      if (result.isSignedIn) {
        this.currentUserChallenge = null;
        return result;
      }

      throw new Error('Password confirmation failed');
    } catch (error) {
      console.error('Complete new password error:', error);
      throw error;
    }
  }

  async signOut() {
    try {
      await amplifySignOut();
      this.currentUserChallenge = null;
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const user = await getCurrentUser();
      
      return {
        username: user.username,
        email: user.signInDetails?.loginId || user.username,
        name: user.username, // Will be updated when we get user attributes
        sub: user.userId,
      };
    } catch (error) {
      return null;
    }
  }

  async getSession() {
    try {
      // This would get the current session with tokens
      // For now, we'll just check if user is authenticated
      const user = await this.getCurrentUser();
      return user ? { isValid: true } : null;
    } catch (error) {
      return null;
    }
  }
}

export const authService = new AuthService();