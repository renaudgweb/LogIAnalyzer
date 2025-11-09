"""
Tests unitaires pour Log Analyzer
"""
import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_loader import load_configuration, validate_configuration, ConfigurationError
from email_sender import send_email, EmailSenderError


class TestConfigLoader(unittest.TestCase):
    """Tests pour le chargement de configuration"""
    
    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'config.ini')
        self.env_file = os.path.join(self.test_dir, '.env')
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_validate_configuration_valid(self):
        """Test validation d'une configuration valide"""
        config = {
            'log_files': ['/var/log/test.log'],
            'email_sender': 'test@example.com',
            'email_receiver': 'receiver@example.com',
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'ai_api_key': 'test_key',
            'smtp_password': 'test_pass',
            'ai_temperature': 0.5,
            'log_check_interval': 300
        }
        
        is_valid, errors = validate_configuration(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_configuration_invalid_email(self):
        """Test validation avec email invalide"""
        config = {
            'log_files': ['/var/log/test.log'],
            'email_sender': 'invalid_email',  # Pas de @
            'email_receiver': 'receiver@example.com',
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'ai_api_key': 'test_key',
            'smtp_password': 'test_pass'
        }
        
        is_valid, errors = validate_configuration(config)
        self.assertFalse(is_valid)
        self.assertTrue(any('email_sender' in err for err in errors))
    
    def test_validate_configuration_invalid_port(self):
        """Test validation avec port invalide"""
        config = {
            'log_files': ['/var/log/test.log'],
            'email_sender': 'test@example.com',
            'email_receiver': 'receiver@example.com',
            'smtp_server': 'smtp.example.com',
            'smtp_port': 99999,  # Port invalide
            'ai_api_key': 'test_key',
            'smtp_password': 'test_pass'
        }
        
        is_valid, errors = validate_configuration(config)
        self.assertFalse(is_valid)
        self.assertTrue(any('smtp_port' in err for err in errors))
    
    def test_validate_configuration_missing_field(self):
        """Test validation avec champ manquant"""
        config = {
            'log_files': ['/var/log/test.log'],
            'email_sender': 'test@example.com',
            # email_receiver manquant
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587
        }
        
        is_valid, errors = validate_configuration(config)
        self.assertFalse(is_valid)
        self.assertTrue(any('email_receiver' in err for err in errors))


class TestEmailSender(unittest.TestCase):
    """Tests pour l'envoi d'emails"""
    
    def setUp(self):
        """Préparation avant chaque test"""
        self.config = {
            'email_sender': 'sender@example.com',
            'email_receiver': 'receiver@example.com',
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_password': 'test_password'
        }
    
    @patch('email_sender.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test envoi d'email réussi"""
        # Mock du serveur SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Appeler la fonction
        result = send_email("Test Subject", "Test Body", self.config)
        
        # Vérifications
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
    
    @patch('email_sender.smtplib.SMTP')
    def test_send_email_authentication_error(self, mock_smtp):
        """Test erreur d'authentification SMTP"""
        # Mock du serveur SMTP avec erreur d'authentification
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Vérifier qu'une exception est levée
        with self.assertRaises(EmailSenderError):
            send_email("Test Subject", "Test Body", self.config)


class TestLogMonitor(unittest.TestCase):
    """Tests pour le monitoring de logs"""
    
    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_log = os.path.join(self.test_dir, 'test.log')
        
        # Créer un fichier de log de test
        with open(self.test_log, 'w') as f:
            f.write("Line 1: Normal log entry\n")
            f.write("Line 2: ERROR: Something went wrong\n")
            f.write("Line 3: WARNING: Potential issue\n")
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_read_new_logs(self):
        """Test lecture de nouvelles lignes de log"""
        from log_monitor import read_new_logs
        
        # Première lecture
        logs, position = read_new_logs(self.test_log, 0)
        self.assertEqual(len(logs), 3)
        self.assertGreater(position, 0)
        
        # Ajouter de nouvelles lignes
        with open(self.test_log, 'a') as f:
            f.write("Line 4: New entry\n")
        
        # Deuxième lecture (seulement les nouvelles lignes)
        new_logs, new_position = read_new_logs(self.test_log, position)
        self.assertEqual(len(new_logs), 1)
        self.assertEqual(new_logs[0].strip(), "Line 4: New entry")
    
    def test_extract_severity_score(self):
        """Test extraction du score de gravité"""
        from log_monitor import extract_severity_score
        
        # Test avec score valide
        analysis = "SEVERITY_SCORE: 8\nCritical issue detected"
        score = extract_severity_score(analysis)
        self.assertEqual(score, 8)
        
        # Test sans score
        analysis = "No score in this analysis"
        score = extract_severity_score(analysis)
        self.assertEqual(score, 0)
        
        # Test avec score hors limites
        analysis = "SEVERITY_SCORE: 15\nInvalid score"
        score = extract_severity_score(analysis)
        self.assertEqual(score, 10)  # Devrait être limité à 10


class TestIntegration(unittest.TestCase):
    """Tests d'intégration"""
    
    def test_full_workflow_mock(self):
        """Test du workflow complet avec mocks"""
        # Ce test simule le workflow complet sans vraies connexions
        # À implémenter selon vos besoins
        pass


def run_tests():
    """Exécute tous les tests"""
    # Créer la suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestConfigLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailSender))
    suite.addTests(loader.loadTestsFromTestCase(TestLogMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retourner le code de sortie approprié
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())