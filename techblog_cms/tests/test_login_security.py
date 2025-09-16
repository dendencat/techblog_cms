from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import time


class LoginSecurityTests(TestCase):
    """Test cases for login security to prevent username enumeration attacks."""
    
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.login_url = reverse('login')  # assuming the login view is named 'login'
    
    def test_login_error_message_consistency(self):
        """Test that error messages are generic for both existing and non-existing users."""
        # Test with non-existing user
        response_nonexistent = self.client.post(self.login_url, {
            'username': 'nonexistentuser',
            'password': 'wrongpassword'
        })
        
        # Test with existing user but wrong password
        response_wrong_password = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Both should return the same generic error message
        self.assertEqual(response_nonexistent.status_code, 401)
        self.assertEqual(response_wrong_password.status_code, 401)
        
        # Check that error messages are the same and generic
        error_msg_nonexistent = response_nonexistent.context.get('error', '')
        error_msg_wrong_password = response_wrong_password.context.get('error', '')
        
        # Both should have the same generic error message
        self.assertEqual(error_msg_nonexistent, error_msg_wrong_password)
        
        # Error message should be generic (not revealing username existence)
        self.assertEqual(error_msg_nonexistent, 'Invalid credentials')
        
    def test_successful_login(self):
        """Test that successful login still works correctly."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect to dashboard on successful login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        
    def test_login_timing_consistency(self):
        """Test that login attempts take similar time regardless of username existence."""
        # This is a basic timing test - in a real security audit, more sophisticated timing analysis would be needed
        
        times_nonexistent = []
        times_wrong_password = []
        
        # Run multiple attempts to get average timing
        for _ in range(5):
            # Time non-existent user login
            start_time = time.time()
            self.client.post(self.login_url, {
                'username': 'nonexistentuser',
                'password': 'wrongpassword'
            })
            times_nonexistent.append(time.time() - start_time)
            
            # Time existing user with wrong password
            start_time = time.time()
            self.client.post(self.login_url, {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            times_wrong_password.append(time.time() - start_time)
        
        # Calculate averages
        avg_nonexistent = sum(times_nonexistent) / len(times_nonexistent)
        avg_wrong_password = sum(times_wrong_password) / len(times_wrong_password)
        
        # The difference should be minimal (less than 50ms)
        # This is a very basic test - sophisticated timing attacks require more precise measurements
        time_difference = abs(avg_nonexistent - avg_wrong_password)
        self.assertLess(time_difference, 0.05, 
                       f"Timing difference too large: {time_difference:.3f}s. "
                       f"Avg nonexistent: {avg_nonexistent:.3f}s, "
                       f"Avg wrong password: {avg_wrong_password:.3f}s")
