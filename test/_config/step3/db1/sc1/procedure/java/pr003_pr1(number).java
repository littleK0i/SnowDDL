import com.snowflake.snowpark_java.*;

class TestClass {
    public Boolean process(Session session, Integer step_id) {
        return step_id > 2;
    }
}
