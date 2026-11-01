import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.io.*;
import java.util.*;

/** Executor JDBC independente: usa os mesmos packages e a mesma base do backend. */
public class OracleSprint4 {
    static Path root;
    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("Uso: OracleSprint4.java PASTA check|prepare|install|seed|test|export");
        root = Path.of(args[0]).toAbsolutePath();
        var props = new Properties();
        props.setProperty("user", require("DB_USERNAME"));
        props.setProperty("password", require("DB_PASSWORD"));
        props.setProperty("oracle.net.CONNECT_TIMEOUT", "10000");
        props.setProperty("oracle.jdbc.ReadTimeout", "60000");
        try (var conn = DriverManager.getConnection(require("DB_URL"), props)) {
            conn.setAutoCommit(false);
            try (var s = conn.createStatement()) { s.execute("BEGIN DBMS_OUTPUT.ENABLE(NULL); END;"); }
            System.out.println("Oracle conectado: " + conn.getMetaData().getDatabaseProductVersion());
            switch (args[1]) {
                case "check" -> query(conn, "SELECT USER usuario, SYS_CONTEXT('USERENV','SERVICE_NAME') servico FROM dual");
                case "prepare" -> {
                    if (conn.getMetaData().getDatabaseMajorVersion() < 19)
                        throw new SQLException("Esta versao da entrega requer Oracle 19c ou superior.");
                    query(conn, "SELECT USER usuario, SYS_CONTEXT('USERENV','SERVICE_NAME') servico FROM dual");
                    int existing;
                    try (var s = conn.createStatement(); var rows = s.executeQuery("SELECT COUNT(*) FROM user_tables WHERE table_name IN ('TB_PERFIL','TB_USUARIO','TB_USUARIO_PERFIL','TB_TUTOR','TB_CLINICA','TB_PET','TB_CONSULTA','TB_EVENTO_SAUDE','TB_VACINA','TB_MEDICAMENTO','CV4_VETERINARIO','CV4_TIPO_SERVICO','CV4_LEITURA_SENSOR','CV4_AUD_PET')")) {
                        rows.next(); existing = rows.getInt(1);
                    }
                    if (existing == 0) script(conn, "sql/2TDSPF_2026_CodigoSql_Integrantes.sql");
                    else if (existing != 14) throw new SQLException("Instalacao parcial ou nomes ocupados: " + existing + "/14 tabelas. Nenhum objeto sera apagado; revisar antes de continuar.");
                    compilation(conn);
                    int records;
                    try (var s = conn.createStatement(); var rows = s.executeQuery("SELECT (SELECT COUNT(*) FROM tb_pet)+(SELECT COUNT(*) FROM tb_tutor)+(SELECT COUNT(*) FROM tb_clinica)+(SELECT COUNT(*) FROM tb_consulta)+(SELECT COUNT(*) FROM CV4_LEITURA_SENSOR) FROM dual")) {
                        rows.next(); records = rows.getInt(1);
                    }
                    if (records == 0) { script(conn, "sql/09_dados_demonstracao.sql"); conn.commit(); }
                    else System.out.println("Dados existentes preservados; a carga nao sera repetida.");
                    script(conn, "sql/10_verificar_objetos.sql");
                    script(conn, "sql/11_testes_transacionais.sql");
                    conn.rollback();
                    export(conn);
                    compilation(conn);
                    query(conn,"SELECT object_name,object_type,status FROM user_objects WHERE object_name LIKE 'PKG_CLYVO%' OR object_name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT') ORDER BY object_name,object_type");
                    System.out.println("Oracle: instalacao, testes e exportacao concluidos; objetos finais VALID.");
                }
                case "install" -> {
                    script(conn, "sql/2TDSPF_2026_CodigoSql_Integrantes.sql");
                    compilation(conn);
                    System.out.println("Instalacao manual concluida; inicie Java com ORACLE_FLYWAY_ENABLED=false.");
                }
                case "seed" -> {
                    query(conn, "SELECT COUNT(*) registros_antes FROM tb_pet");
                    script(conn, "sql/09_dados_demonstracao.sql");
                    conn.commit();
                    System.out.println("Carga ficticia instalada.");
                }
                case "test" -> {
                    compilation(conn);
                    script(conn, "sql/10_verificar_objetos.sql");
                    script(conn, "sql/11_testes_transacionais.sql");
                    conn.rollback();
                }
                case "export" -> { compilation(conn); export(conn); }
                default -> throw new IllegalArgumentException("Acao desconhecida");
            }
            output(conn);
        }
    }
    static void export(Connection conn) throws Exception {
        try (var call = conn.prepareCall("{call PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON(?,?)}")) {
            call.setNull(1, Types.NUMERIC); call.registerOutParameter(2, Types.CLOB); call.execute();
            var clob = call.getClob(2);
            if (clob == null) throw new SQLException("Procedure retornou CLOB nulo");
            Path dest = root.resolve("dataset/2TDSPF_2026_Atendimentos.json");
            Files.createDirectories(dest.getParent());
            Path temporary = dest.resolveSibling(dest.getFileName()+".tmp");
            try (var reader=clob.getCharacterStream(); var writer=Files.newBufferedWriter(temporary,StandardCharsets.UTF_8)) {
                reader.transferTo(writer);
            } finally { clob.free(); }
            Files.move(temporary,dest,StandardCopyOption.REPLACE_EXISTING);
            System.out.println("Dataset exportado pelo package: " + dest);
        }
        query(conn,"SELECT COUNT(*) quantidade FROM tb_consulta");
        query(conn,"SELECT COUNT(*) quantidade FROM CV4_ATENDIMENTO");
        query(conn,"SELECT SUM(valor) total_2026 FROM tb_consulta WHERE status='CONCLUIDA' AND EXTRACT(YEAR FROM data_consulta)=2026");
    }
    static String require(String key) {
        String value=System.getenv(key);
        if(value==null || value.isBlank()) throw new IllegalArgumentException("Configure " + key + " localmente.");
        return value;
    }
    static void compilation(Connection c) throws SQLException {
        // A sincronizacao IDENTITY da carga pode invalidar dependentes sem criar
        // USER_ERRORS. Recompila somente os objetos conhecidos deste projeto.
        for (String name : List.of("PKG_CLYVO_JSON","PKG_CLYVO_CLINICO","PKG_CLYVO_RELATORIOS","PKG_CLYVO_AUDITORIA","PKG_CLYVOVET")) {
            try (var s=c.prepareStatement("SELECT status FROM user_objects WHERE object_name=? AND object_type='PACKAGE BODY'")) {
                s.setString(1,name);
                boolean invalid;
                try (var rows=s.executeQuery()) { invalid=rows.next() && "INVALID".equals(rows.getString(1)); }
                if (invalid) try (var ddl=c.createStatement()) { ddl.execute("ALTER PACKAGE "+name+" COMPILE BODY"); }
            }
        }
        for (String name : List.of("TRG_CV4_AUD_PET","TRG_CV4_CONSULTA_CAT")) {
            try (var s=c.prepareStatement("SELECT status FROM user_objects WHERE object_name=? AND object_type='TRIGGER'")) {
                s.setString(1,name);
                boolean invalid;
                try (var rows=s.executeQuery()) { invalid=rows.next() && "INVALID".equals(rows.getString(1)); }
                if (invalid) try (var ddl=c.createStatement()) { ddl.execute("ALTER TRIGGER "+name+" COMPILE"); }
            }
        }
        try(var s=c.createStatement(); var rows=s.executeQuery("SELECT name,line,text FROM user_errors WHERE name LIKE 'PKG_CLYVO%' OR name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT')")) {
            var errors=new StringBuilder();
            while(rows.next()) errors.append(rows.getString(1)).append(':').append(rows.getInt(2)).append(' ').append(rows.getString(3)).append('\n');
            if(!errors.isEmpty()) throw new SQLException("Objetos invalidos:\n"+errors);
        }
        Set<String> expected = new HashSet<>();
        for (String name : List.of("PKG_CLYVO_JSON","PKG_CLYVO_CLINICO","PKG_CLYVO_RELATORIOS","PKG_CLYVO_AUDITORIA","PKG_CLYVOVET")) {
            expected.add(name+":PACKAGE"); expected.add(name+":PACKAGE BODY");
        }
        expected.add("TRG_CV4_AUD_PET:TRIGGER"); expected.add("TRG_CV4_CONSULTA_CAT:TRIGGER");
        try (var s=c.createStatement(); var rows=s.executeQuery("SELECT object_name,object_type,status FROM user_objects WHERE object_name LIKE 'PKG_CLYVO%' OR object_name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT')")) {
            while (rows.next()) {
                if (!"VALID".equals(rows.getString(3))) throw new SQLException("Objeto invalido: "+rows.getString(1));
                expected.remove(rows.getString(1)+":"+rows.getString(2));
            }
        }
        if (!expected.isEmpty()) throw new SQLException("Objetos ausentes: "+expected);
    }
    static void query(Connection c,String sql) throws SQLException {
        try(var s=c.createStatement(); var rows=s.executeQuery(sql)) { printRows(rows); }
    }
    static void printRows(ResultSet rows) throws SQLException {
        var meta=rows.getMetaData();
        while(rows.next()) {
            var line=new StringJoiner(" | ");
            for(int i=1;i<=meta.getColumnCount();i++) line.add(meta.getColumnLabel(i)+"="+rows.getString(i));
            System.out.println(line);
        }
    }
    static void script(Connection c,String relative) throws Exception {
        var text=Files.readString(root.resolve(relative),StandardCharsets.UTF_8);
        var pending=new StringBuilder(); boolean block=false;
        for(String line:text.split("\\R")) {
            String trim=line.strip();
            if(trim.isEmpty() || trim.startsWith("--") || trim.matches("(?i)^(SET|WHENEVER|PROMPT|COLUMN|SHOW)\\b.*")) continue;
            if(pending.isEmpty()) block=trim.matches("(?i)^(DECLARE|BEGIN)\\b.*") || trim.matches("(?i)^CREATE\\s+OR\\s+REPLACE\\s+(PACKAGE|TRIGGER)\\b.*");
            if(block && trim.equals("/")) { execute(c,pending.toString(),true); pending.setLength(0); block=false; continue; }
            pending.append(line).append('\n');
            if(!block && trim.endsWith(";")) {
                String sql=pending.toString().strip();
                execute(c,sql.substring(0,sql.length()-1),false); pending.setLength(0);
            }
        }
        if(!pending.toString().isBlank()) throw new IllegalStateException("SQL incompleto em "+relative);
        output(c);
    }
    static void execute(Connection c,String sql,boolean block) throws SQLException {
        try(var s=c.createStatement()) {
            if(s.execute(sql)) try(var rows=s.getResultSet()) { printRows(rows); }
        } catch(SQLException ex) {
            // Nao inclui a instrucao nem parametros nos logs: podem conter dados pessoais.
            throw new SQLException("Falha SQL (codigo "+ex.getErrorCode()+"): "+ex.getMessage(),ex.getSQLState(),ex.getErrorCode(),ex);
        }
    }
    static void output(Connection c) throws SQLException {
        try(var call=c.prepareCall("BEGIN DBMS_OUTPUT.GET_LINE(?,?); END;")) {
            call.registerOutParameter(1,Types.VARCHAR); call.registerOutParameter(2,Types.INTEGER);
            for(int i=0;i<10000;i++) { call.execute(); if(call.getInt(2)!=0) break; System.out.println(call.getString(1)); }
        }
    }
}
