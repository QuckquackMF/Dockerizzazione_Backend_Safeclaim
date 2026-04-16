USE gestione_assicurazioni;

CREATE TABLE IF NOT EXISTS Assicuratore (
    id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(50) NOT NULL, cognome VARCHAR(50) NOT NULL,
    cf VARCHAR(16) UNIQUE NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, psw VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS Assicurazione (
    id INT PRIMARY KEY AUTO_INCREMENT, ragione_sociale VARCHAR(100) NOT NULL, nome VARCHAR(100), telefono VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS Automobilista (
    id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(50) NOT NULL, cognome VARCHAR(50) NOT NULL,
    cf VARCHAR(16) UNIQUE NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, psw VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS Azienda (
    id INT PRIMARY KEY AUTO_INCREMENT, ragione_sociale VARCHAR(100) NOT NULL, partita_iva VARCHAR(11) UNIQUE NOT NULL,
    sede_legale VARCHAR(200), email VARCHAR(100), telefono VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS Documenti_Anagrafica (
    id INT PRIMARY KEY AUTO_INCREMENT, entita_tipo ENUM('automobilista', 'perito', 'officina', 'assicurazione', 'soccorso') NOT NULL,
    entita_id INT NOT NULL, mongo_doc_id VARCHAR(24) NOT NULL, tipo_documento VARCHAR(50) NOT NULL,
    descrizione VARCHAR(255), data_inserimento DATETIME DEFAULT CURRENT_TIMESTAMP, data_scadenza DATE
);
CREATE TABLE IF NOT EXISTS Officina (
    id INT PRIMARY KEY AUTO_INCREMENT, ragione_sociale VARCHAR(100) NOT NULL, citta VARCHAR(50),
    indirizzo VARCHAR(200), telefono VARCHAR(20), email VARCHAR(100), latitudine DECIMAL(10, 8), longitudine DECIMAL(11, 8)
);
CREATE TABLE IF NOT EXISTS Perito (
    id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(50) NOT NULL, cognome VARCHAR(50) NOT NULL,
    cf VARCHAR(16) UNIQUE, email VARCHAR(100) UNIQUE NOT NULL, psw VARCHAR(255), latitudine DECIMAL(10, 8), longitudine DECIMAL(11, 8)
);
CREATE TABLE IF NOT EXISTS Veicolo (
    id INT PRIMARY KEY AUTO_INCREMENT, targa VARCHAR(10) UNIQUE NOT NULL, n_telaio VARCHAR(17) UNIQUE,
    marca VARCHAR(50), modello VARCHAR(50), anno_immatricolazione YEAR, automobilista_id INT, azienda_id INT,
    CONSTRAINT fk_veicolo_automobilista FOREIGN KEY (automobilista_id) REFERENCES Automobilista(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_veicolo_azienda FOREIGN KEY (azienda_id) REFERENCES Azienda(id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS Polizza (
    id INT PRIMARY KEY AUTO_INCREMENT, n_polizza VARCHAR(50) UNIQUE NOT NULL, compagnia_assicurativa VARCHAR(100),
    data_inizio DATE NOT NULL, data_scadenza DATE NOT NULL, massimale DECIMAL(12, 2),
    tipo_copertura ENUM('RCA', 'Kasko', 'Full') DEFAULT 'RCA', veicolo_id INT, assicuratore_id INT,
    documento_mongo_id VARCHAR(24),
    CONSTRAINT fk_polizza_veicolo FOREIGN KEY (veicolo_id) REFERENCES Veicolo(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_polizza_assicuratore FOREIGN KEY (assicuratore_id) REFERENCES Assicuratore(id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS Polizza_Documenti (
    id INT PRIMARY KEY AUTO_INCREMENT, polizza_id INT NOT NULL, mongo_doc_id VARCHAR(24) NOT NULL,
    tipo_documento ENUM('polizza_pdf', 'quietanza') NOT NULL, descrizione VARCHAR(255),
    data_inserimento DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_polizza_documenti_polizza FOREIGN KEY (polizza_id) REFERENCES Polizza(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- DATI DI TEST
INSERT IGNORE INTO Assicuratore (nome, cognome, cf, email, psw) VALUES ('NomeA1','CognomeA1','CFASSICURAT00001','ass1@test.it','hash_psw');
INSERT IGNORE INTO Automobilista (nome, cognome, cf, email, psw) VALUES ('Auto1','Cognome1','CFDRIVER0000001','driver1@test.it','hash_psw');
INSERT IGNORE INTO Officina (ragione_sociale, citta, telefono, latitudine, longitudine) VALUES ('Garage 1','Milano','02111111',45.4642,9.1900);
INSERT IGNORE INTO Perito (nome, cognome, cf, email, latitudine, longitudine) VALUES ('Perito1','Rossi1','CFPERITO0000001','perito1@studiovr.it',45.0,9.0);
INSERT IGNORE INTO Veicolo (targa, n_telaio, marca, modello, anno_immatricolazione, automobilista_id) VALUES ('AA001BB','VIN00000000000001','Fiat','Panda',2020,1);
INSERT IGNORE INTO Polizza (n_polizza, compagnia_assicurativa, data_inizio, data_scadenza, massimale, veicolo_id, assicuratore_id) VALUES ('POL-00001','Generali','2024-01-01','2025-01-01',5000000.00,1,1);