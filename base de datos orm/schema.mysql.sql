CREATE TABLE `t_cliente` (
  `CLI_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `CLI_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `CLI_PER_ID` int(11) NOT NULL,
  PRIMARY KEY (`CLI_ID`),
  UNIQUE KEY `CLI_UUID_UNIQUE` (`CLI_UUID`),
  KEY `fk_T_CLIENTE_T_PERSONA1_idx` (`CLI_PER_ID`),
  CONSTRAINT `fk_T_CLIENTE_T_PERSONA1` FOREIGN KEY (`CLI_PER_ID`) REFERENCES `t_persona` (`PER_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_contacto` (
  `CONT_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `CONT_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `CONT_TIPO_DATO` varchar(15) NOT NULL,
  `CONT_CONTENIDO` varchar(45) NOT NULL,
  `CONT_PROV_ID` int(11) NOT NULL,
  PRIMARY KEY (`CONT_ID`),
  UNIQUE KEY `CONT_UUID_UNIQUE` (`CONT_UUID`),
  KEY `fk_T_CONTACTO_T_PROVEEDORES1_idx` (`CONT_PROV_ID`),
  CONSTRAINT `fk_T_CONTACTO_T_PROVEEDORES1` FOREIGN KEY (`CONT_PROV_ID`) REFERENCES `t_proveedores` (`PROV_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_cotizaciones` (
  `COT_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `COT_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros ',
  `COT_PRO_CODIGO` varchar(45) NOT NULL,
  `COT_PRO_NOMBRE` varchar(45) NOT NULL,
  `COT_PRO_CANTIDAD` int(11) NOT NULL,
  `COT_PRO_PRECIO` int(11) NOT NULL,
  `COT_TOTAL_PAGAR` int(11) NOT NULL,
  `COT_USUA_ID` int(11) NOT NULL,
  `COT_CLI_ID` int(11) NOT NULL,
  PRIMARY KEY (`COT_ID`),
  UNIQUE KEY `COT_UUID_UNIQUE` (`COT_UUID`),
  KEY `fk_T_COTIZACIONES_T_USUARIO1_idx` (`COT_USUA_ID`),
  KEY `fk_T_COTIZACIONES_T_CLIENTE1_idx` (`COT_CLI_ID`),
  CONSTRAINT `fk_T_COTIZACIONES_T_CLIENTE1` FOREIGN KEY (`COT_CLI_ID`) REFERENCES `t_cliente` (`CLI_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_COTIZACIONES_T_USUARIO1` FOREIGN KEY (`COT_USUA_ID`) REFERENCES `t_usuarios` (`USUA_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_detalles_etc` (
  `DET_ETC_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `DET_ETC_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `DET_ETC_NOMBRE` varchar(45) NOT NULL,
  `DET_ETC_ETC_ID` int(11) NOT NULL,
  `DET_ETC_PER_ID` int(11) NOT NULL,
  PRIMARY KEY (`DET_ETC_ID`),
  UNIQUE KEY `DET_ETC_UUID_UNIQUE` (`DET_ETC_UUID`),
  KEY `fk_T_DETALLES_ETC_T_ESTADO_TIPOS_CATEGORIAS1_idx` (`DET_ETC_ETC_ID`),
  KEY `fk_T_DETALLES_ETC_T_PERSONA1_idx` (`DET_ETC_PER_ID`),
  CONSTRAINT `fk_T_DETALLES_ETC_T_ESTADO_TIPOS_CATEGORIAS1` FOREIGN KEY (`DET_ETC_ETC_ID`) REFERENCES `t_estado_tipos_categorias` (`ETC_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_DETALLES_ETC_T_PERSONA1` FOREIGN KEY (`DET_ETC_PER_ID`) REFERENCES `t_persona` (`PER_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_estado_tipos_categorias` (
  `ETC_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `ETC_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `ETC_NOMBRE` varchar(45) NOT NULL,
  PRIMARY KEY (`ETC_ID`),
  UNIQUE KEY `ETC_UUID_UNIQUE` (`ETC_UUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_insumos` (
  `INS_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `INS_UUID` varchar(40) NOT NULL,
  `INS_CODIGO` varchar(45) NOT NULL,
  `INS_NOMBRE` varchar(45) NOT NULL,
  `INS_CANTIDAD` int(11) NOT NULL,
  `INS_PRECIO` int(11) NOT NULL,
  `INS_ESTADO` varchar(45) NOT NULL,
  `INS_USUA_ID` int(11) NOT NULL,
  `INS_PROV_ID` int(11) NOT NULL,
  `INS_DET_ETC_ID` int(11) NOT NULL,
  PRIMARY KEY (`INS_ID`),
  UNIQUE KEY `INS_UUID_UNIQUE` (`INS_UUID`),
  UNIQUE KEY `INS_CODIGO_UNIQUE` (`INS_CODIGO`),
  KEY `fk_T_INSUMOS_T_USUARIO1_idx` (`INS_USUA_ID`),
  KEY `fk_T_INSUMOS_T_PROVEEDORES1_idx` (`INS_PROV_ID`),
  KEY `fk_T_INSUMOS_T_DETALLES_ETC1_idx` (`INS_DET_ETC_ID`),
  CONSTRAINT `fk_T_INSUMOS_T_DETALLES_ETC1` FOREIGN KEY (`INS_DET_ETC_ID`) REFERENCES `t_detalles_etc` (`DET_ETC_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_INSUMOS_T_PROVEEDORES1` FOREIGN KEY (`INS_PROV_ID`) REFERENCES `t_proveedores` (`PROV_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_INSUMOS_T_USUARIO1` FOREIGN KEY (`INS_USUA_ID`) REFERENCES `t_usuarios` (`USUA_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_persona` (
  `PER_ID` int(11) NOT NULL AUTO_INCREMENT,
  `PER_UUID` varchar(45) NOT NULL,
  `PER_NOMBRE` varchar(100) NOT NULL,
  `PER_SEG_NOMBRE` varchar(45) DEFAULT NULL,
  `PER_PRI_APELLIDO` varchar(45) DEFAULT NULL,
  `PER_SEG_APELLIDO` varchar(45) DEFAULT NULL,
  `PER_CORREO` varchar(100) NOT NULL,
  `PER_DIRECCION` varchar(45) NOT NULL,
  `PER_IDENTIFICACION` int(11) NOT NULL,
  `PER_TELEFONO` int(11) NOT NULL,
  PRIMARY KEY (`PER_ID`),
  UNIQUE KEY `PER_UUID_UNIQUE` (`PER_UUID`),
  UNIQUE KEY `PER_IDENTIFICACION_UNIQUE` (`PER_IDENTIFICACION`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_produ_insum` (
  `PROINSU_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `PROINSU_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `PROINSU_CANTIDAD` int(11) NOT NULL,
  `PROINSU_PROD_ID` int(11) NOT NULL,
  `PROINSU_INS_ID` int(11) NOT NULL,
  PRIMARY KEY (`PROINSU_ID`),
  UNIQUE KEY `PROINSU_UUID_UNIQUE` (`PROINSU_UUID`),
  KEY `fk_PRODU_ISUM_T_PRODUCTOS1_idx` (`PROINSU_PROD_ID`),
  KEY `fk_PRODU_ISUM_T_INSUMOS1_idx` (`PROINSU_INS_ID`),
  CONSTRAINT `fk_PRODU_ISUM_T_INSUMOS1` FOREIGN KEY (`PROINSU_INS_ID`) REFERENCES `t_insumos` (`INS_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_PRODU_ISUM_T_PRODUCTOS1` FOREIGN KEY (`PROINSU_PROD_ID`) REFERENCES `t_productos` (`PROD_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_productos` (
  `PROD_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `PROD_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `PROD_CODIGO` varchar(45) NOT NULL,
  `PROD_NOMBRE` varchar(45) NOT NULL,
  `PROD_CANTIDAD` int(11) NOT NULL,
  `PROD_PRECIO` int(11) NOT NULL,
  `PROD_ESTADO` varchar(45) NOT NULL,
  `PROD_USUA_ID` int(11) NOT NULL,
  `PROD_DET_ETC_ID` int(11) NOT NULL,
  PRIMARY KEY (`PROD_ID`),
  UNIQUE KEY `PROD_UUID_UNIQUE` (`PROD_UUID`),
  UNIQUE KEY `PROD_CODIGO_UNIQUE` (`PROD_CODIGO`),
  KEY `fk_T_PRODUCTOS_T_USUARIO1_idx` (`PROD_USUA_ID`),
  KEY `fk_T_PRODUCTOS_T_DETALLES_ETC1_idx` (`PROD_DET_ETC_ID`),
  CONSTRAINT `fk_T_PRODUCTOS_T_DETALLES_ETC1` FOREIGN KEY (`PROD_DET_ETC_ID`) REFERENCES `t_detalles_etc` (`DET_ETC_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_PRODUCTOS_T_USUARIO1` FOREIGN KEY (`PROD_USUA_ID`) REFERENCES `t_usuarios` (`USUA_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_proveedores` (
  `PROV_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `PROV_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `PROV_PER_ID` int(11) NOT NULL,
  PRIMARY KEY (`PROV_ID`),
  UNIQUE KEY `PROV_UUID_UNIQUE` (`PROV_UUID`),
  KEY `fk_T_PROVEEDORES_T_PERSONA1_idx` (`PROV_PER_ID`),
  CONSTRAINT `fk_T_PROVEEDORES_T_PERSONA1` FOREIGN KEY (`PROV_PER_ID`) REFERENCES `t_persona` (`PER_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_usuarios` (
  `USUA_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten.\n\n',
  `USUA_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros ',
  `USUA_NOMBRE` varchar(60) NOT NULL COMMENT 'contiene el numero de identificacion del usuario la sea cedula de ciudadania o algun otro documento que acredite su identidad',
  `USUA_CORREO` varchar(100) NOT NULL,
  `USUA_CONTRASEÑA` varchar(45) NOT NULL COMMENT 'es la contraseña del usuario con la cual obtiene acceso a la base de datos para modificar su contenido',
  `USUA_ESTADO` varchar(45) NOT NULL,
  `USUA_DET_ETC_ID` int(11) NOT NULL,
  PRIMARY KEY (`USUA_ID`),
  UNIQUE KEY `USUA_UUID_UNIQUE` (`USUA_UUID`),
  KEY `fk_T_USUARIOS_T_DETALLES_ETC1_idx` (`USUA_DET_ETC_ID`),
  CONSTRAINT `fk_T_USUARIOS_T_DETALLES_ETC1` FOREIGN KEY (`USUA_DET_ETC_ID`) REFERENCES `t_detalles_etc` (`DET_ETC_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_vent_prod` (
  `VENPRO_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `VENPRO_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `VENPRO_CANTIDAD` int(11) NOT NULL,
  `VENPRO_VENT_ID` int(11) NOT NULL,
  `VENPRO_PROD_ID` int(11) NOT NULL,
  PRIMARY KEY (`VENPRO_ID`),
  UNIQUE KEY `VENPRO_UUID_UNIQUE` (`VENPRO_UUID`),
  KEY `fk_T_VENT_PROD_T_VENTAS1_idx` (`VENPRO_VENT_ID`),
  KEY `fk_T_VENT_PROD_T_PRODUCTOS1_idx` (`VENPRO_PROD_ID`),
  CONSTRAINT `fk_T_VENT_PROD_T_PRODUCTOS1` FOREIGN KEY (`VENPRO_PROD_ID`) REFERENCES `t_productos` (`PROD_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_VENT_PROD_T_VENTAS1` FOREIGN KEY (`VENPRO_VENT_ID`) REFERENCES `t_ventas` (`VENT_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE `t_ventas` (
  `VENT_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'valor único asignado a cada registro (fila) de una tabla. Su función principal es distinguir de manera inequívoca cada elemento, sin importar si otros datos (como nombres o direcciones) se repiten',
  `VENT_UUID` varchar(40) NOT NULL COMMENT 'código alfanumérico de 36 caracteres dividida por guioneslos UUID son aleatorios. Esto evita que un usuario pueda deducir o adivinar la cantidad total de registros',
  `VENT_FECHA` date NOT NULL,
  `VENT_USUA_ID` int(11) NOT NULL,
  `VENT_CLI_ID` int(11) NOT NULL,
  PRIMARY KEY (`VENT_ID`),
  UNIQUE KEY `VENT_UUID_UNIQUE` (`VENT_UUID`),
  KEY `fk_T_VENTAS_T_USUARIO_idx` (`VENT_USUA_ID`),
  KEY `fk_T_VENTAS_T_CLIENTE1_idx` (`VENT_CLI_ID`),
  CONSTRAINT `fk_T_VENTAS_T_CLIENTE1` FOREIGN KEY (`VENT_CLI_ID`) REFERENCES `t_cliente` (`CLI_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_T_VENTAS_T_USUARIO` FOREIGN KEY (`VENT_USUA_ID`) REFERENCES `t_usuarios` (`USUA_ID`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;
